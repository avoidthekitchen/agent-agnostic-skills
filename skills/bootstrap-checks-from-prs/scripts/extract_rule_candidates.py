#!/usr/bin/env python3
"""Extract recurring rule candidates from artifacts/pr-scan.json."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RULE_LIBRARY: list[dict[str, Any]] = [
    {
        "id": "security-auth-invariants",
        "category": "security invariants",
        "topic": "auth-guard-consistency",
        "description": "Ensure protected routes consistently enforce authentication and authorization checks.",
        "look_for": [
            "Protected handlers missing auth/authorization guards",
            "Inconsistent permission checks across similar endpoints",
        ],
        "keywords": ["auth", "authorize", "authorization", "permission", "rbac", "acl", "jwt", "token"],
        "risk": 0.96,
        "detectability": 0.80,
    },
    {
        "id": "security-input-validation",
        "category": "security invariants",
        "topic": "input-validation-boundaries",
        "description": "Validate untrusted input at API and persistence boundaries.",
        "look_for": [
            "Request input used without schema or guard validation",
            "Unescaped or unchecked user input flowing into storage/query layers",
        ],
        "keywords": ["validate", "validation", "sanitize", "injection", "sql", "xss", "escape"],
        "risk": 0.97,
        "detectability": 0.78,
    },
    {
        "id": "compliance-sensitive-logging",
        "category": "compliance requirements",
        "topic": "sensitive-data-in-logs",
        "description": "Avoid logging secrets and regulated personal data.",
        "look_for": [
            "Sensitive fields logged without masking/redaction",
            "PII or credential material emitted in debug/error logs",
        ],
        "keywords": ["pii", "phi", "gdpr", "compliance", "audit", "mask", "redact", "log"],
        "risk": 0.93,
        "detectability": 0.76,
    },
    {
        "id": "performance-n-plus-one",
        "category": "performance best practices",
        "topic": "n-plus-one-patterns",
        "description": "Prevent N+1 access patterns and repeated expensive work in loops.",
        "look_for": [
            "Repeated DB/network calls inside loops",
            "Missing batching/prefetch where repeated access is predictable",
        ],
        "keywords": ["n+1", "loop", "batch", "prefetch", "query", "performance", "cache"],
        "risk": 0.74,
        "detectability": 0.71,
    },
    {
        "id": "performance-pagination-guard",
        "category": "performance best practices",
        "topic": "pagination-for-large-reads",
        "description": "Ensure large list endpoints support pagination or bounded reads.",
        "look_for": [
            "Large list endpoints returning unbounded result sets",
            "Missing pagination parameters for collection reads",
        ],
        "keywords": ["pagination", "page", "limit", "offset", "cursor", "unbounded"],
        "risk": 0.70,
        "detectability": 0.82,
    },
    {
        "id": "migration-deprecated-apis",
        "category": "migration/deprecation reminders",
        "topic": "deprecated-api-usage",
        "description": "Track and migrate deprecated API usage to supported alternatives.",
        "look_for": [
            "New call sites using deprecated APIs",
            "Deprecated code paths expanded without migration notes",
        ],
        "keywords": ["deprecated", "deprecate", "legacy", "migration", "sunset", "remove"],
        "risk": 0.72,
        "detectability": 0.75,
    },
    {
        "id": "style-error-handling-convention",
        "category": "style conventions outside linters",
        "topic": "error-handling-consistency",
        "description": "Keep error handling behavior and messaging consistent across similar code paths.",
        "look_for": [
            "Error paths that bypass shared handling conventions",
            "Inconsistent error typing/message shape in similar modules",
        ],
        "keywords": ["error", "exception", "handle", "consistency", "message", "convention"],
        "risk": 0.58,
        "detectability": 0.63,
    },
]


STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "please",
    "that",
    "the",
    "this",
    "to",
    "we",
    "with",
    "you",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def normalize_text(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text).strip().lower()
    return collapsed


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_+-]+", text.lower())


def short_snippet(text: str, limit: int = 180) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] if slug else "candidate"


def top_level_path(path: str | None) -> str | None:
    if not path:
        return None
    cleaned = path.strip("/")
    if not cleaned or "/" not in cleaned:
        return None
    return cleaned.split("/", 1)[0]


def path_allowed(path: str | None, include_paths: list[str], exclude_paths: list[str]) -> bool:
    if path is None:
        return not include_paths
    normalized = path.lstrip("/")
    if include_paths and not any(normalized.startswith(p.lstrip("/")) for p in include_paths):
        return False
    if any(normalized.startswith(p.lstrip("/")) for p in exclude_paths):
        return False
    return True


def classify_rule(text: str) -> dict[str, Any] | None:
    tokens = set(tokenize(text))
    best_rule: dict[str, Any] | None = None
    best_score = 0
    for rule in RULE_LIBRARY:
        score = 0
        for keyword in rule["keywords"]:
            if " " in keyword:
                if keyword in text:
                    score += 1
            elif keyword in tokens:
                score += 1
        if score > best_score:
            best_score = score
            best_rule = rule
    return best_rule if best_score > 0 else None


def fallback_generic_rule(text: str) -> dict[str, Any] | None:
    terms = [tok for tok in tokenize(text) if tok not in STOPWORDS and len(tok) > 2]
    if len(terms) < 5:
        return None
    topic_terms = terms[:5]
    topic = "-".join(topic_terms)
    phrase = " ".join(topic_terms)
    return {
        "id": f"anti-pattern-{topic}",
        "category": "known team anti-patterns",
        "topic": topic,
        "description": f"Avoid recurring anti-pattern related to '{phrase}'.",
        "look_for": [
            f"Code patterns resembling: {phrase}",
            "Repeated review feedback indicating maintainability risk",
        ],
        "risk": 0.55,
        "detectability": 0.45,
    }


def build_candidates(scan: dict[str, Any], min_frequency: int) -> list[dict[str, Any]]:
    include_paths = list(scan.get("metadata", {}).get("include_paths", []))
    exclude_paths = list(scan.get("metadata", {}).get("exclude_paths", []))

    aggregate: dict[str, dict[str, Any]] = {}

    for pr in scan.get("pull_requests", []):
        pr_number = int(pr.get("number", 0))
        pr_url = pr.get("url")

        evidence_rows: list[dict[str, Any]] = []
        for comment in pr.get("review_comments", []):
            evidence_rows.append(
                {
                    "source_type": "review_comment",
                    "text": str(comment.get("body") or ""),
                    "path": comment.get("path"),
                    "url": comment.get("url"),
                    "line": comment.get("line"),
                }
            )
        for comment in pr.get("issue_comments", []):
            evidence_rows.append(
                {
                    "source_type": "issue_comment",
                    "text": str(comment.get("body") or ""),
                    "path": None,
                    "url": comment.get("url"),
                    "line": None,
                }
            )

        for file_item in pr.get("changed_files", []):
            path = file_item.get("path")
            if not path_allowed(path, include_paths, exclude_paths):
                continue
            patch = str(file_item.get("patch") or "")
            if patch:
                evidence_rows.append(
                    {
                        "source_type": "diff",
                        "text": patch,
                        "path": path,
                        "url": pr_url,
                        "line": None,
                    }
                )

        for row in evidence_rows:
            text = normalize_text(row["text"])
            if not text:
                continue
            path = row.get("path")
            if not path_allowed(path, include_paths, exclude_paths):
                continue

            rule = classify_rule(text)
            if rule is None:
                rule = fallback_generic_rule(text)
            if rule is None:
                continue

            candidate_id = str(rule["id"])
            if candidate_id not in aggregate:
                aggregate[candidate_id] = {
                    "candidate_id": candidate_id,
                    "category": rule["category"],
                    "topic": rule["topic"],
                    "description": rule["description"],
                    "look_for": list(rule["look_for"]),
                    "risk": float(rule["risk"]),
                    "detectability": float(rule["detectability"]),
                    "evidence": [],
                }

            aggregate[candidate_id]["evidence"].append(
                {
                    "pr_number": pr_number,
                    "pr_url": pr_url,
                    "source_type": row["source_type"],
                    "path": path,
                    "line": row.get("line"),
                    "url": row.get("url"),
                    "snippet": short_snippet(text),
                }
            )

    compiled: list[dict[str, Any]] = []
    for candidate in aggregate.values():
        evidence = candidate["evidence"]
        prs = sorted({int(item["pr_number"]) for item in evidence})
        frequency = len(prs)

        scope_counter: Counter[str] = Counter()
        scoped_evidence = 0
        for item in evidence:
            top = top_level_path(item.get("path"))
            if top:
                scope_counter[top] += 1
                scoped_evidence += 1

        if scope_counter:
            scope_path, scope_hits = scope_counter.most_common(1)[0]
            if scoped_evidence > 0 and scope_hits / scoped_evidence >= 0.60:
                scope = {"kind": "subtree", "path": scope_path}
            else:
                scope = {"kind": "global"}
        else:
            scope = {"kind": "global"}

        risk = float(candidate["risk"])
        detectability = float(candidate["detectability"])
        freq_norm = min(1.0, frequency / max(min_frequency, 1))
        confidence = round((freq_norm * 0.45 + risk * 0.35 + detectability * 0.20) * 100, 1)

        promoted = frequency >= min_frequency or (risk >= 0.90 and frequency >= 1)

        if detectability >= 0.80 and frequency >= min_frequency:
            false_positive_risk = "low"
        elif detectability >= 0.60 and frequency >= max(1, min_frequency - 1):
            false_positive_risk = "medium"
        else:
            false_positive_risk = "high"

        if risk >= 0.97 and frequency >= max(3, min_frequency + 1):
            severity_default = "critical"
        elif risk >= 0.90 and frequency >= 1:
            severity_default = "high"
        elif risk < 0.55:
            severity_default = "low"
        else:
            severity_default = "medium"

        if not promoted:
            recommended_action = "drop"
        elif confidence >= 75 and false_positive_risk != "high":
            recommended_action = "keep"
        else:
            recommended_action = "refine"

        check_name = slugify(candidate["candidate_id"])

        compiled.append(
            {
                "candidate_id": candidate["candidate_id"],
                "check_name": check_name,
                "category": candidate["category"],
                "topic": candidate["topic"],
                "description": candidate["description"],
                "look_for": candidate["look_for"],
                "scope": scope,
                "source_prs": prs,
                "evidence_count": len(evidence),
                "evidence": evidence[:12],
                "scores": {
                    "frequency": frequency,
                    "risk": risk,
                    "detectability": detectability,
                    "scope_specificity": 1.0 if scope["kind"] == "subtree" else 0.5,
                },
                "confidence_score": confidence,
                "estimated_false_positive_risk": false_positive_risk,
                "severity_default": severity_default,
                "promoted": promoted,
                "recommended_action": recommended_action,
            }
        )

    compiled.sort(
        key=lambda item: (
            0 if item["promoted"] else 1,
            -float(item["confidence_score"]),
            -int(item["scores"]["frequency"]),
            str(item["candidate_id"]),
        )
    )
    return compiled


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="artifacts/pr-scan.json", help="Input PR scan JSON")
    parser.add_argument("--output", default="artifacts/rule-candidates.json", help="Output path")
    parser.add_argument("--min-frequency", type=int, default=2, help="Promotion frequency threshold")
    parser.add_argument("--max-candidates", type=int, default=100, help="Optional cap after ranking")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scan = read_json(Path(args.input))
    metadata = scan.get("metadata", {})
    min_frequency = args.min_frequency or int(metadata.get("min_frequency", 2))

    candidates = build_candidates(scan=scan, min_frequency=min_frequency)
    if args.max_candidates > 0:
        candidates = candidates[: args.max_candidates]

    payload = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo": metadata.get("repo"),
            "source_pr_count": metadata.get("actual_pr_count"),
            "min_frequency": min_frequency,
            "include_paths": metadata.get("include_paths", []),
            "exclude_paths": metadata.get("exclude_paths", []),
        },
        "candidates": candidates,
    }

    output_path = Path(args.output)
    write_json(output_path, payload)

    promoted = sum(1 for candidate in candidates if candidate["promoted"])
    print(f"Wrote {len(candidates)} candidates ({promoted} promoted) to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
