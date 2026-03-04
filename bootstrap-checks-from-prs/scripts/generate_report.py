#!/usr/bin/env python3
"""Generate artifacts/check-bootstrap-report.md from pipeline artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def maybe_read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return read_json(path)


def recommendation_emoji(value: str) -> str:
    normalized = value.lower()
    if normalized == "keep":
        return "✅"
    if normalized == "refine":
        return "⚠️"
    return "🛑"


def build_report(
    candidates_payload: dict[str, Any],
    drafts_payload: dict[str, Any],
    writes_payload: dict[str, Any] | None,
) -> str:
    candidates = candidates_payload.get("candidates", [])
    drafts = drafts_payload.get("drafts", [])
    write_map = {}
    if writes_payload:
        for row in writes_payload.get("results", []):
            write_map[str(row.get("candidate_id"))] = row

    promoted = [item for item in candidates if item.get("promoted")]
    dropped = [item for item in candidates if not item.get("promoted")]
    refine = [item for item in promoted if item.get("recommended_action") == "refine"]
    keep = [item for item in promoted if item.get("recommended_action") == "keep"]

    lines: list[str] = []
    lines.append("# Check Bootstrap Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Repo: {candidates_payload.get('metadata', {}).get('repo', 'unknown')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total candidates mined: {len(candidates)}")
    lines.append(f"- Promoted candidates: {len(promoted)}")
    lines.append(f"- Draft checks rendered: {len(drafts)}")
    lines.append(f"- Keep now: {len(keep)}")
    lines.append(f"- Needs tuning: {len(refine)}")
    lines.append(f"- Dropped: {len(dropped)}")
    lines.append("")

    lines.append("## Proposed Checks")
    lines.append("")
    if not drafts:
        lines.append("No draft checks were generated.")
        lines.append("")
    else:
        for draft in drafts:
            candidate_id = str(draft.get("candidate_id"))
            candidate = next((item for item in promoted if str(item.get("candidate_id")) == candidate_id), None)
            written = write_map.get(candidate_id)
            confidence = candidate.get("confidence_score") if candidate else "n/a"
            noise_risk = candidate.get("estimated_false_positive_risk") if candidate else "n/a"
            recommendation = candidate.get("recommended_action") if candidate else "refine"
            source_prs = candidate.get("source_prs", []) if candidate else []
            source_ref = ", ".join(f"#{num}" for num in source_prs[:8]) if source_prs else "n/a"

            lines.append(f"### {draft.get('check_name')}")
            lines.append("")
            lines.append(f"- File: `{written.get('written_path')}`" if written else f"- Planned file: `{draft.get('target_directory')}/{draft.get('filename')}`")
            lines.append(f"- Confidence: {confidence}")
            lines.append(f"- Estimated false-positive risk: {noise_risk}")
            lines.append(f"- Recommendation: {recommendation_emoji(str(recommendation))} {recommendation}")
            lines.append(f"- Source PRs: {source_ref}")
            lines.append("")

    lines.append("## Likely Noisy Checks to Tune First")
    lines.append("")
    noisy = [item for item in promoted if item.get("estimated_false_positive_risk") == "high"]
    if not noisy:
        lines.append("- None flagged as high risk.")
    else:
        for item in noisy:
            lines.append(f"- `{item.get('check_name')}` (confidence {item.get('confidence_score')})")
    lines.append("")

    lines.append("## Dropped Candidates")
    lines.append("")
    if not dropped:
        lines.append("- None")
    else:
        for item in dropped[:20]:
            lines.append(
                f"- `{item.get('check_name')}`: insufficient recurrence (frequency {item.get('scores', {}).get('frequency', 'n/a')})"
            )
    lines.append("")

    lines.append("## Calibration Notes")
    lines.append("")
    lines.append("- Run generated checks against a holdout recent PR/diff.")
    lines.append("- Tighten wording for any high-noise checks before broad rollout.")
    lines.append("- Re-run bootstrap periodically and diff outputs to detect drift.")
    lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", default="artifacts/rule-candidates.json", help="Candidates artifact")
    parser.add_argument("--drafts", default="artifacts/check-drafts.json", help="Draft checks artifact")
    parser.add_argument("--writes", default="artifacts/write-result.json", help="Write results artifact (optional)")
    parser.add_argument("--output", default="artifacts/check-bootstrap-report.md", help="Markdown report output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates_payload = read_json(Path(args.candidates))
    drafts_payload = read_json(Path(args.drafts))
    writes_payload = maybe_read_json(Path(args.writes))

    report = build_report(
        candidates_payload=candidates_payload,
        drafts_payload=drafts_payload,
        writes_payload=writes_payload,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print(f"Wrote report to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
