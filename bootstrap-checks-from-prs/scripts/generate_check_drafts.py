#!/usr/bin/env python3
"""Render promoted rule candidates into draft check payloads."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "check"


def yaml_quote(value: str) -> str:
    escaped = value.replace("\"", "\\\"")
    return f'"{escaped}"'


def category_slug(category: str) -> str:
    return slugify(category).replace("-", "-")[:24]


def topic_slug(topic: str, check_name: str) -> str:
    source = topic or check_name
    return slugify(source)[:36]


def render_markdown(candidate: dict[str, Any], severity: str) -> str:
    look_for = candidate.get("look_for", [])
    if not look_for:
        look_for = [candidate.get("description", "Review for repeated team concern.")]

    source_prs = candidate.get("source_prs", [])
    rationale_line = ", ".join(f"#{number}" for number in source_prs[:8])
    if not rationale_line:
        rationale_line = "(insufficient PR evidence attached)"

    examples: list[str] = []
    for row in candidate.get("evidence", [])[:2]:
        snippet = str(row.get("snippet", "")).strip()
        if snippet:
            examples.append(snippet)
    if not examples:
        examples = ["No short snippet available; review linked PR comments for context."]

    look_for_lines = "\n".join(f"- {item}" for item in look_for)
    example_lines = "\n".join(f"- {item}" for item in examples)

    return "\n".join(
        [
            "---",
            f"name: {candidate['check_name']}",
            f"description: {yaml_quote(candidate['description'])}",
            f"severity-default: {severity}",
            "tools: [Grep, Read]",
            "---",
            "",
            "Look for:",
            "",
            look_for_lines,
            "",
            "Report:",
            "",
            "- File and line",
            "- Why this matters",
            "- Suggested remediation direction",
            "",
            "Rationale (derived from recent PRs):",
            "",
            f"- Repeated evidence in PR {rationale_line}",
            "",
            "Examples:",
            "",
            example_lines,
            "",
            "Non-examples:",
            "",
            "- Existing code that already applies the same guard/validation/convention consistently",
            "",
        ]
    )


def determine_target_directory(scope: dict[str, Any]) -> str:
    if scope.get("kind") == "subtree" and scope.get("path"):
        path = str(scope["path"]).strip("/")
        return f"{path}/.agents/checks"
    return ".agents/checks"


def resolve_severity(candidate: dict[str, Any], default_severity: str) -> str:
    candidate_severity = str(candidate.get("severity_default") or "").lower().strip()
    if candidate_severity in {"low", "medium", "high", "critical"}:
        return candidate_severity
    return default_severity


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="artifacts/rule-candidates.json", help="Input candidate JSON")
    parser.add_argument("--output", default="artifacts/check-drafts.json", help="Output path")
    parser.add_argument("--max-checks", type=int, default=10, help="Maximum draft checks to emit")
    parser.add_argument("--default-severity", default="medium", help="Fallback severity")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = read_json(Path(args.input))
    metadata = payload.get("metadata", {})

    if args.max_checks <= 0:
        raise ValueError("--max-checks must be greater than 0")

    default_severity = str(args.default_severity).lower().strip()
    if default_severity not in {"low", "medium", "high", "critical"}:
        raise ValueError("--default-severity must be one of low|medium|high|critical")

    promoted = [c for c in payload.get("candidates", []) if c.get("promoted")]
    selected = promoted[: args.max_checks]

    drafts: list[dict[str, Any]] = []
    for index, candidate in enumerate(selected, start=1):
        order = index * 10
        category_part = category_slug(str(candidate.get("category", "general")))
        topic_part = topic_slug(str(candidate.get("topic", "")), str(candidate.get("check_name", "check")))
        filename = f"{order:02d}-{category_part}-{topic_part}.md"
        severity = resolve_severity(candidate, default_severity)

        drafts.append(
            {
                "candidate_id": candidate.get("candidate_id"),
                "check_name": candidate.get("check_name"),
                "filename": filename,
                "scope": candidate.get("scope", {"kind": "global"}),
                "target_directory": determine_target_directory(candidate.get("scope", {})),
                "confidence_score": candidate.get("confidence_score"),
                "estimated_false_positive_risk": candidate.get("estimated_false_positive_risk"),
                "recommended_action": candidate.get("recommended_action"),
                "source_prs": candidate.get("source_prs", []),
                "severity_default": severity,
                "content": render_markdown(candidate, severity),
            }
        )

    output_payload = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo": metadata.get("repo"),
            "source_pr_count": metadata.get("source_pr_count"),
            "max_checks": args.max_checks,
            "default_severity": default_severity,
            "promoted_candidates": len(promoted),
            "emitted_drafts": len(drafts),
        },
        "drafts": drafts,
    }

    output_path = Path(args.output)
    write_json(output_path, output_payload)
    print(f"Wrote {len(drafts)} draft check payloads to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
