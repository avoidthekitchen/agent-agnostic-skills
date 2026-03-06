# agent-agnostic-skills

This repository contains my proposed agent skills built to the [`agentskills.io`](https://agentskills.io/specification) specification.

## Install a Skill

Per [`skills.sh`](https://skills.sh/docs/cli) docs/FAQ, install skills with the `skills` CLI:

```bash
npx skills add <owner>/<repo>
```

Example for installing all the skills in this repository:

```bash
npx skills add avoidthekitchen/agent-agnostic-skills
```

To install just the bootstrap checks skill:

```bash
npx skills add avoidthekitchen/agent-agnostic-skills@bootstrap-checks-from-prs
```

To install all the RPI skill set:

```bash
npx skills add avoidthekitchen/agent-agnostic-skills@rpi-research
npx skills add avoidthekitchen/agent-agnostic-skills@rpi-plan
npx skills add avoidthekitchen/agent-agnostic-skills@rpi-implement-plan
```

Notes:

- Skills are supported by popular coding agents such as Claude Code, Cursor, and Windsurf (check per-skill compatibility).
- Review a skill's repository before installing and use your normal security review process.

## Included Skills

- `bootstrap-checks-from-prs`
- `rpi-research`
- `rpi-plan`
- `rpi-implement-plan`

## RPI Skills: Research -> Plan -> Implement

[RPI (Research, Plan, Implement)](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md), introduced by HumanLayer, is a structured workflow for agents that helps with more complex changes with documented research and plan documents. This helps agents by:
- Surfacing agent assumptions that you can correct
- Tracking plans and implementation so that the agent does not lose context
- Creating durable artifacts for both humans and agents to reference later

This repository includes a coordinated set of three RPI workflow skills adapted from [akurkin's  Claude-specific command workflows](https://github.com/teambrilliant/claude-research-plan-implement). 

### `rpi-research`

- Performs deep codebase research with citations.
- Produces a research memo at `rpi/research/TIMESTAMP_topic.md`.
- Uses Windows-safe timestamps in filenames (`YYYYMMDDTHHMMSSZ`).

### `rpi-plan`

- Turns requirements and research into a phased implementation plan.
- Produces a plan at `rpi/plans/TIMESTAMP_descriptive_name.md`.
- Uses Windows-safe timestamps in filenames (`YYYYMMDDTHHMMSSZ`).
- Requires explicit unchecked implementation tasks (`- [ ]`) for planned changes.

### `rpi-implement-plan`

- Executes an approved plan phase-by-phase.
- Runs verification after each phase and updates plan checkboxes as work is completed.

## Bootstrap Checks: `bootstrap-checks-from-prs`

`bootstrap-checks-from-prs` mines merged PR history and bootstraps draft "checks" so teams can quickly codify recurring review expectations for agents. This uses an agent agnostic checks folder structured proposed by [Amp Code](https://ampcode.com/manual#checks).

What it does:

- Collects merged PR metadata, changed files, non-bot review comments, issue comments, and check-run hints.
- Extracts recurring review patterns and scores candidates by frequency, risk, detectability, and scope.
- Renders high-signal check drafts and writes them to:
  - `.agents/checks/*.md` for repo-wide checks
  - `<area>/.agents/checks/*.md` for subtree-scoped checks
- Includes a workflow step to ensure root `AGENTS.md` references `.agents/checks/` for code reviews (creating it if missing).
- Generates evidence artifacts and a reviewer-focused bootstrap report.

Skill location:

- `skills/bootstrap-checks-from-prs/SKILL.md`

Core pipeline scripts:

- `skills/bootstrap-checks-from-prs/scripts/collect_prs.py`
- `skills/bootstrap-checks-from-prs/scripts/extract_rule_candidates.py`
- `skills/bootstrap-checks-from-prs/scripts/generate_check_drafts.py`
- `skills/bootstrap-checks-from-prs/scripts/write_checks.py`
- `skills/bootstrap-checks-from-prs/scripts/generate_report.py`

### Quick Run (from `skills/bootstrap-checks-from-prs/`)

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
- The skill workflow includes an explicit `AGENTS.md` update step so review agents load checks from `.agents/checks/`.

### Re-running the Skill

Running the pipeline again is safe, with a few expected behaviors:

- Artifact files in `artifacts/` are overwritten on each run with fresh outputs.
- Generated check markdown files are never silently overwritten; name collisions create `-draft` / `-draft-N` variants.
- If you want versioned artifacts per run, pass custom output paths to the scripts (for example `--output artifacts/pr-scan-2026-03-04.json`).
