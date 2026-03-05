#!/usr/bin/env python3
"""Write draft checks to .agents/checks with collision-safe naming.

Also ensures Agents.md (or existing AGENTS.md) references generated .agents/checks folders for code review.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


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
    parser.add_argument("--input", default="artifacts/check-drafts.json", help="Draft check payload input")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--result-output", default="artifacts/write-result.json", help="Write result JSON")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; emit planned paths only")
    return parser.parse_args()


def instructions_for_check_dir(relative_check_dir: Path) -> str:
    check_dir = relative_check_dir.as_posix()
    return (
        "## Code review checks\n"
        f"When performing code reviews, consult checks in `{check_dir}` and apply all relevant guidance.\n"
    )


def append_agents_reference_if_missing(repo_root: Path, relative_check_dir: Path, dry_run: bool) -> dict[str, Any]:
    scope_root = relative_check_dir.parent.parent
    candidate_paths = [
        repo_root / scope_root / "Agents.md",
        repo_root / scope_root / "AGENTS.md",
    ]
    agents_path = candidate_paths[0]
    existed_before = False
    for candidate_path in candidate_paths:
        if candidate_path.exists():
            agents_path = candidate_path
            existed_before = True
            break

    check_dir = relative_check_dir.as_posix()
    instruction_block = instructions_for_check_dir(relative_check_dir)

    if existed_before:
        existing_text = agents_path.read_text(encoding="utf-8")
        if check_dir in existing_text:
            return {
                "agents_path": str(agents_path.relative_to(repo_root)),
                "check_directory": check_dir,
                "status": "already_referenced",
                "existed_before": True,
                "dry_run": dry_run,
            }
        separator = "\n" if existing_text.endswith("\n") else "\n\n"
        updated_text = f"{existing_text}{separator}{instruction_block}"
        status = "appended"
    else:
        updated_text = instruction_block
        status = "created"

    if not dry_run:
        agents_path.parent.mkdir(parents=True, exist_ok=True)
        agents_path.write_text(updated_text, encoding="utf-8")

    return {
        "agents_path": str(agents_path.relative_to(repo_root)),
        "check_directory": check_dir,
        "status": status,
        "existed_before": existed_before,
        "dry_run": dry_run,
    }


def main() -> int:
    args = parse_args()
    payload = read_json(Path(args.input))
    repo_root = Path(args.repo_root).resolve()

    results: list[dict[str, Any]] = []
    touched_check_dirs: set[str] = set()
    for draft in payload.get("drafts", []):
        target_dir = ensure_safe_relative(str(draft.get("target_directory", ".agents/checks")))
        filename = ensure_safe_relative(str(draft.get("filename", "draft-check.md"))).name

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
        touched_check_dirs.add(target_dir.as_posix())

    agents_updates = [
        append_agents_reference_if_missing(repo_root, Path(check_dir), args.dry_run)
        for check_dir in sorted(touched_check_dirs)
    ]

    output_payload = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo_root": str(repo_root),
            "draft_count": len(payload.get("drafts", [])),
            "written_count": len(results),
            "dry_run": args.dry_run,
        },
        "results": results,
        "agents_updates": agents_updates,
    }

    result_output = Path(args.result_output)
    write_json(result_output, output_payload)

    created_count = sum(1 for item in results if not item["dry_run"])
    print(f"Processed {len(results)} drafts ({created_count} files written)")
    print(f"Wrote write-result metadata to {result_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
