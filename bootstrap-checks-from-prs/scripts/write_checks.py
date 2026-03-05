#!/usr/bin/env python3
"""Write draft checks to .agents/checks with collision-safe naming.

Also ensures root AGENTS.md references .agents/checks for code reviews.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AGENTS_BLOCK_START = "<!-- bootstrap-checks-from-prs:checks:start -->"
AGENTS_BLOCK_END = "<!-- bootstrap-checks-from-prs:checks:end -->"
AGENTS_CHECKS_SECTION = """## Code Review Checks

When performing code reviews, load and apply checks from `.agents/checks/`.
Also apply subtree-scoped checks from `<subtree>/.agents/checks/` when reviewing files in that subtree.
"""


def managed_agents_block() -> str:
    return (
        f"{AGENTS_BLOCK_START}\n{AGENTS_CHECKS_SECTION.strip()}\n{AGENTS_BLOCK_END}\n"
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def ensure_safe_relative(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        raise ValueError(f"Absolute target path is not allowed: {path}")
    parts = candidate.parts
    if any(part == ".." for part in parts):
        raise ValueError(f"Parent directory traversal is not allowed: {path}")
    return candidate


def next_collision_safe_path(base_path: Path) -> tuple[Path, bool]:
    if not base_path.exists():
        return base_path, False

    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    first = parent / f"{stem}-draft{suffix}"
    if not first.exists():
        return first, True

    counter = 2
    while True:
        candidate = parent / f"{stem}-draft-{counter}{suffix}"
        if not candidate.exists():
            return candidate, True
        counter += 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="artifacts/check-drafts.json",
        help="Draft check payload input",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument(
        "--result-output",
        default="artifacts/write-result.json",
        help="Write result JSON",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write files; emit planned paths only",
    )
    return parser.parse_args()


def ensure_agents_md(repo_root: Path, dry_run: bool) -> dict[str, Any]:
    agents_path = repo_root / "AGENTS.md"
    result = {
        "path": "AGENTS.md",
        "action": "unchanged",
        "dry_run": dry_run,
    }

    block = managed_agents_block()

    if not agents_path.exists():
        content = "# AGENTS.md\n\n" + block
        if not dry_run:
            agents_path.write_text(content, encoding="utf-8")
        result["action"] = "created"
        return result

    existing = agents_path.read_text(encoding="utf-8")
    start = existing.find(AGENTS_BLOCK_START)
    end = existing.find(AGENTS_BLOCK_END)

    if start != -1 and end != -1 and start < end:
        end_index = end + len(AGENTS_BLOCK_END)
        if end_index < len(existing) and existing[end_index : end_index + 1] == "\n":
            end_index += 1
        updated = existing[:start] + block + existing[end_index:]
    else:
        suffix = "\n\n" if existing and not existing.endswith("\n\n") else ""
        updated = existing + suffix + block

    if updated == existing:
        return result

    if not dry_run:
        agents_path.write_text(updated, encoding="utf-8")
    result["action"] = "updated"
    return result


def main() -> int:
    args = parse_args()
    payload = read_json(Path(args.input))
    repo_root = Path(args.repo_root).resolve()

    results: list[dict[str, Any]] = []
    for draft in payload.get("drafts", []):
        target_dir = ensure_safe_relative(
            str(draft.get("target_directory", ".agents/checks"))
        )
        filename = ensure_safe_relative(
            str(draft.get("filename", "draft-check.md"))
        ).name

        absolute_dir = (repo_root / target_dir).resolve()
        absolute_path = absolute_dir / filename
        safe_path, collided = next_collision_safe_path(absolute_path)

        if not args.dry_run:
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(str(draft.get("content", "")), encoding="utf-8")

        results.append(
            {
                "candidate_id": draft.get("candidate_id"),
                "check_name": draft.get("check_name"),
                "requested_path": str((absolute_dir / filename).relative_to(repo_root)),
                "written_path": str(safe_path.relative_to(repo_root)),
                "collision_detected": collided,
                "dry_run": args.dry_run,
            }
        )

    agents_md_result = ensure_agents_md(repo_root=repo_root, dry_run=args.dry_run)

    output_payload = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo_root": str(repo_root),
            "draft_count": len(payload.get("drafts", [])),
            "written_count": len(results),
            "dry_run": args.dry_run,
            "agents_md": agents_md_result,
        },
        "results": results,
    }

    result_output = Path(args.result_output)
    write_json(result_output, output_payload)

    created_count = sum(1 for item in results if not item["dry_run"])
    print(f"Processed {len(results)} drafts ({created_count} files written)")
    print(
        f"AGENTS.md action: {agents_md_result['action']} ({agents_md_result['path']})"
    )
    print(f"Wrote write-result metadata to {result_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
