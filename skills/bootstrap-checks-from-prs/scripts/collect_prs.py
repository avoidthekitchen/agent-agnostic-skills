#!/usr/bin/env python3
"""Collect merged PR evidence and normalize into artifacts/pr-scan.json."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def run_command(args: list[str]) -> str:
    try:
        completed = subprocess.run(args, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{stderr}") from exc
    return completed.stdout


def gh_api(endpoint: str, params: dict[str, Any] | None = None) -> Any:
    args = ["gh", "api", "--method", "GET", "-H", "Accept: application/vnd.github+json", endpoint]
    if params:
        for key, value in params.items():
            args.extend(["-f", f"{key}={value}"])
    output = run_command(args)
    return json.loads(output)


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def is_bot_user(user: dict[str, Any] | None) -> bool:
    if not user:
        return False
    login = str(user.get("login", "")).lower()
    user_type = str(user.get("type", "")).lower()
    return user_type == "bot" or login.endswith("[bot]")


def resolve_repo(repo: str | None) -> str:
    if repo:
        return repo
    payload = json.loads(run_command(["gh", "repo", "view", "--json", "nameWithOwner"]))
    resolved = payload.get("nameWithOwner")
    if not resolved:
        raise RuntimeError("Unable to resolve repo from local context via `gh repo view`.")
    return str(resolved)


def resolve_default_branch(repo: str) -> str:
    payload = gh_api(f"/repos/{repo}")
    branch = payload.get("default_branch")
    if not branch:
        raise RuntimeError(f"Unable to resolve default branch for {repo}.")
    return str(branch)


def fetch_paginated_list(endpoint: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    page = 1
    while True:
        data = gh_api(endpoint, params={"per_page": 100, "page": page})
        if not isinstance(data, list):
            raise RuntimeError(f"Expected list from {endpoint}, got {type(data).__name__}.")
        if not data:
            break
        results.extend(data)
        if len(data) < 100:
            break
        page += 1
    return results


def fetch_merged_prs(
    repo: str,
    limit: int,
    base_branch: str,
    include_labels: list[str],
    exclude_bots: bool,
    time_window_days: int | None,
    max_pages: int,
) -> list[dict[str, Any]]:
    include_label_set = {label.lower() for label in include_labels}
    cutoff = None
    if time_window_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=time_window_days)

    collected: list[dict[str, Any]] = []
    page = 1
    while page <= max_pages and len(collected) < limit:
        pulls = gh_api(
            f"/repos/{repo}/pulls",
            params={
                "state": "closed",
                "sort": "updated",
                "direction": "desc",
                "per_page": 100,
                "page": page,
            },
        )
        if not isinstance(pulls, list) or not pulls:
            break

        for pr in pulls:
            merged_at_raw = pr.get("merged_at")
            merged_at = parse_utc(merged_at_raw)
            if not merged_at:
                continue
            if pr.get("base", {}).get("ref") != base_branch:
                continue
            if exclude_bots and is_bot_user(pr.get("user")):
                continue
            if cutoff and merged_at < cutoff:
                continue

            labels = [str(label.get("name", "")) for label in pr.get("labels", [])]
            if include_label_set and not include_label_set.intersection({l.lower() for l in labels}):
                continue

            collected.append(pr)

        page += 1

    deduped: dict[int, dict[str, Any]] = {}
    for pr in collected:
        raw_number = pr.get("number")
        if raw_number is None:
            continue
        number = int(raw_number)
        deduped[number] = pr

    ordered = sorted(
        deduped.values(),
        key=lambda item: parse_utc(item.get("merged_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return ordered[:limit]


def normalize_files(repo: str, pr_number: int) -> list[dict[str, Any]]:
    endpoint = f"/repos/{repo}/pulls/{pr_number}/files"
    files = fetch_paginated_list(endpoint)
    normalized: list[dict[str, Any]] = []
    for file_item in files:
        patch = str(file_item.get("patch") or "")
        if len(patch) > 2000:
            patch = patch[:2000] + "..."
        normalized.append(
            {
                "path": file_item.get("filename"),
                "status": file_item.get("status"),
                "additions": file_item.get("additions", 0),
                "deletions": file_item.get("deletions", 0),
                "changes": file_item.get("changes", 0),
                "patch": patch,
            }
        )
    return normalized


def normalize_review_comments(repo: str, pr_number: int) -> list[dict[str, Any]]:
    endpoint = f"/repos/{repo}/pulls/{pr_number}/comments"
    comments = fetch_paginated_list(endpoint)
    normalized: list[dict[str, Any]] = []
    for comment in comments:
        normalized.append(
            {
                "author": comment.get("user", {}).get("login"),
                "body": comment.get("body") or "",
                "path": comment.get("path"),
                "line": comment.get("line") or comment.get("original_line"),
                "created_at": comment.get("created_at"),
                "url": comment.get("html_url"),
            }
        )
    return normalized


def normalize_issue_comments(repo: str, pr_number: int) -> list[dict[str, Any]]:
    endpoint = f"/repos/{repo}/issues/{pr_number}/comments"
    comments = fetch_paginated_list(endpoint)
    normalized: list[dict[str, Any]] = []
    for comment in comments:
        normalized.append(
            {
                "author": comment.get("user", {}).get("login"),
                "body": comment.get("body") or "",
                "created_at": comment.get("created_at"),
                "url": comment.get("html_url"),
            }
        )
    return normalized


def normalize_check_runs(repo: str, merge_commit_sha: str | None) -> list[dict[str, Any]]:
    if not merge_commit_sha:
        return []
    endpoint = f"/repos/{repo}/commits/{merge_commit_sha}/check-runs"
    try:
        payload = gh_api(endpoint, params={"per_page": 100})
    except RuntimeError:
        return []
    runs = payload.get("check_runs", []) if isinstance(payload, dict) else []
    normalized: list[dict[str, Any]] = []
    for run in runs:
        normalized.append(
            {
                "name": run.get("name"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "url": run.get("details_url"),
            }
        )
    return normalized


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="owner/name (optional; inferred from local context if omitted)")
    parser.add_argument("--x", type=int, default=30, help="Number of merged PRs to analyze")
    parser.add_argument("--base-branch", help="Base branch to filter PRs")
    parser.add_argument("--time-window-days", type=int, help="Only include PRs merged within this window")
    parser.add_argument("--min-frequency", type=int, default=2, help="Stored in metadata for downstream scripts")
    parser.add_argument("--exclude-bots", dest="exclude_bots", action="store_true", default=True)
    parser.add_argument("--include-bots", dest="exclude_bots", action="store_false")
    parser.add_argument("--include-label", action="append", default=[], help="Label filter (repeatable)")
    parser.add_argument("--include-path", action="append", default=[], help="Path prefix include filter")
    parser.add_argument("--exclude-path", action="append", default=[], help="Path prefix exclude filter")
    parser.add_argument("--max-checks", type=int, default=10, help="Stored in metadata for downstream scripts")
    parser.add_argument("--default-severity", default="medium", help="Stored in metadata for downstream scripts")
    parser.add_argument("--max-pages", type=int, default=20, help="Maximum closed-PR pages to scan")
    parser.add_argument("--output", default="artifacts/pr-scan.json", help="Output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = resolve_repo(args.repo)
    base_branch = args.base_branch or resolve_default_branch(repo)

    merged_prs = fetch_merged_prs(
        repo=repo,
        limit=args.x,
        base_branch=base_branch,
        include_labels=args.include_label,
        exclude_bots=args.exclude_bots,
        time_window_days=args.time_window_days,
        max_pages=args.max_pages,
    )

    normalized_prs: list[dict[str, Any]] = []
    for pr in merged_prs:
        number = int(pr["number"])
        print(f"Collecting PR #{number} ...", file=sys.stderr)

        normalized_prs.append(
            {
                "number": number,
                "title": pr.get("title") or "",
                "body": pr.get("body") or "",
                "labels": [str(label.get("name", "")) for label in pr.get("labels", [])],
                "author": pr.get("user", {}).get("login"),
                "merged_at": pr.get("merged_at"),
                "url": pr.get("html_url"),
                "base_branch": pr.get("base", {}).get("ref"),
                "changed_files": normalize_files(repo, number),
                "review_comments": normalize_review_comments(repo, number),
                "issue_comments": normalize_issue_comments(repo, number),
                "check_runs": normalize_check_runs(repo, pr.get("merge_commit_sha")),
            }
        )

    payload = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo": repo,
            "requested_pr_count": args.x,
            "actual_pr_count": len(normalized_prs),
            "base_branch": base_branch,
            "time_window_days": args.time_window_days,
            "min_frequency": args.min_frequency,
            "exclude_bots": args.exclude_bots,
            "include_labels": args.include_label,
            "include_paths": args.include_path,
            "exclude_paths": args.exclude_path,
            "max_checks": args.max_checks,
            "default_severity": args.default_severity,
        },
        "pull_requests": normalized_prs,
    }

    output_path = Path(args.output)
    write_json(output_path, payload)
    print(f"Wrote normalized PR scan to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
