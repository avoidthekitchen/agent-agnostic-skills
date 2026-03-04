# agent-agnostic-skills

This repository contains agent skills built to the [`agentskills.io`](https://agentskills.io/specification) specification.

## Install a Skill

Per [`skills.sh`](https://skills.sh/docs/cli) docs/FAQ, install skills with the `skills` CLI:

```bash
npx skills add <owner>/<repo>
```

Examples:

```bash
npx skills add avoidthekitchen/agent-agnostic-skills
```

To install this specific skill from this repository:

```bash
npx skills add avoidthekitchen/agent-agnostic-skills@bootstrap-checks-from-prs
```

Notes:

- Skills are supported by popular coding agents such as Claude Code, Cursor, and Windsurf (check per-skill compatibility).
- Review a skill's repository before installing and use your normal security review process.

## Included Skill: `bootstrap-checks-from-prs`

`bootstrap-checks-from-prs` mines merged PR history and bootstraps draft Amp checks so teams can quickly codify recurring review expectations.

What it does:

- Collects merged PR metadata, changed files, review comments, issue comments, and check-run hints.
- Extracts recurring review patterns and scores candidates by frequency, risk, detectability, and scope.
- Renders high-signal check drafts and writes them to:
  - `.agents/checks/*.md` for repo-wide checks
  - `<area>/.agents/checks/*.md` for subtree-scoped checks
- Generates evidence artifacts and a reviewer-focused bootstrap report.

Skill location:

- `bootstrap-checks-from-prs/SKILL.md`

Core pipeline scripts:

- `bootstrap-checks-from-prs/scripts/collect_prs.py`
- `bootstrap-checks-from-prs/scripts/extract_rule_candidates.py`
- `bootstrap-checks-from-prs/scripts/generate_check_drafts.py`
- `bootstrap-checks-from-prs/scripts/write_checks.py`
- `bootstrap-checks-from-prs/scripts/generate_report.py`

### Quick Run (from `bootstrap-checks-from-prs/`)

```bash
python3 scripts/collect_prs.py --x 30
python3 scripts/extract_rule_candidates.py --min-frequency 2
python3 scripts/generate_check_drafts.py --max-checks 10 --default-severity medium
python3 scripts/write_checks.py
python3 scripts/generate_report.py
```

Expected artifacts:

- `artifacts/pr-scan.json`
- `artifacts/rule-candidates.json`
- `artifacts/check-drafts.json`
- `artifacts/write-result.json`
- `artifacts/check-bootstrap-report.md`

Notes:

- Requires `python3` and authenticated `gh` CLI access.
- Check file collisions are handled safely with `-draft` suffixing; existing checks are not overwritten silently.
