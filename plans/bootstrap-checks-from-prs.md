# Plan: Skill to Bootstrap Checks from Recent PRs (Auto-Write Drafts)

## Goal

Create an agent skill that analyzes the last `X` merged pull requests in a repository and auto-writes draft check files into `.agents/checks/` so reviewers can quickly approve, tune, or discard them.

## Implementation Status

- [x] Create `bootstrap-checks-from-prs/SKILL.md` with invocation contract and safe defaults
- [x] Implement `scripts/collect_prs.py` to gather and normalize PR evidence into `artifacts/pr-scan.json`
- [x] Implement `scripts/extract_rule_candidates.py` to cluster and score candidates into `artifacts/rule-candidates.json`
- [x] Implement `scripts/generate_check_drafts.py` to render draft checks into `artifacts/check-drafts.json`
- [x] Implement `scripts/write_checks.py` to write checks with collision safety
- [x] Implement `scripts/generate_report.py` to write `artifacts/check-bootstrap-report.md`
- [x] Add `references/taxonomy.md` and `references/check-template.md`
- [x] Validate scripts end-to-end on sample/real inputs and confirm plan deliverables are met

## Non-Goals

- Auto-applying fixes or code mods
- Auto-merging generated checks
- Building a full static-analysis framework in v1

## Standards Alignment

- **Agent Skills spec (`agentskills.io`)**
  - Skill is a directory with required `SKILL.md`.
  - `SKILL.md` includes YAML frontmatter (`name`, `description`) and markdown instructions.
  - Optional support files can live in `scripts/`, `references/`, and `assets/`.
- **Amp checks spec (`ampcode.com/manual#checks`)**
  - Checks are markdown files in `.agents/checks/` with YAML frontmatter.
  - Required frontmatter: `name`.
  - Optional frontmatter: `description`, `severity-default`, `tools`.
  - Scope rules:
    - `.agents/checks/` at repo root applies globally.
    - `subdir/.agents/checks/` applies to that subtree.
    - Same-named deeper checks override parent checks.

## Skill Definition

- **Skill name:** `bootstrap-checks-from-prs`
- **Primary behavior:** mine recent PR history for recurring review expectations and write draft checks immediately into `.agents/checks/` (and subtree check folders when appropriate).
- **Trigger phrases in description:**
  - "bootstrap checks from PRs"
  - "suggest checks from review history"
  - "generate .agents/checks"
  - "derive team conventions from pull requests"

## Inputs and Defaults

- **Required**
  - `repo` (owner/name) OR local repository context (run inside a checked-out repo where `gh` works)
- **Optional (with defaults)**
  - `x`: `30` (number of recently merged PRs to analyze)
  - `base_branch`: repo default branch
  - `time_window_days`: none (use latest merged PRs)
  - `min_frequency`: `2` (recommend `2-3`)
  - `exclude_bots`: `true`
  - `include_labels`: []
  - `include_paths`: [] (only consider patterns concentrated under these paths)
  - `exclude_paths`: [] (ignore patterns concentrated under these paths)
  - `max_checks`: `10` (emit a small, high-signal initial set)
  - `default_severity`: `medium` (escalate to `high`/`critical` only with strong security/compliance evidence)

## Output Contract

- **Generated check files**
  - `.agents/checks/*.md` (repo-wide patterns)
  - `subdir/.agents/checks/*.md` (area-specific patterns)
- **Evidence artifacts**
  - `artifacts/pr-scan.json` (normalized PR/review data used for mining)
  - `artifacts/check-bootstrap-report.md` (why each check was suggested, with PR references)

Each generated check must follow the Amp checks format:

- YAML frontmatter
  - `name` (required)
  - `description` (optional)
  - `severity-default` (optional: `low|medium|high|critical`)
  - `tools` (optional)
- Markdown body with:
  - patterns to detect
  - rationale/impact
  - finding format: file + line + why + fix direction

## End-to-End Workflow

### Phase 1: Collect PR Signals

1. Use `gh`/GitHub API to fetch last `X` merged PRs (optionally constrained by `time_window_days`).
2. Collect per PR:
   - title/body/labels/author/mergedAt
   - changed files and diff stats
   - review comments and issue comments
   - CI/check failure clues where available
3. Normalize all of the above into `artifacts/pr-scan.json`.

### Phase 2: Normalize, Cluster, and Score Patterns

1. Extract repeated statements and patterns from comments and changes.
2. Cluster into canonical buckets:
   - performance best practices
   - known team anti-patterns
   - security invariants
   - migration/deprecation reminders
   - style conventions outside linters
   - compliance requirements
3. Score each candidate pattern by:
   - frequency (how often it appears across PRs)
   - severity/risk (impact of missing it)
   - detectability (can a check reliably spot it)
   - scope (repo-wide vs subtree-specific)

### Phase 3: Promote Candidates to Draft Checks

1. Promote if one of:
   - appears in at least `min_frequency` PRs (recommend `2-3`), or
   - is strong security/compliance evidence even at lower frequency
2. Add false-positive guards where possible (tighten scope, add preconditions, request evidence before reporting).
3. Select top patterns and emit at most `max_checks` checks (favor precision over coverage).
4. Default severity to `default_severity`; escalate only with strong evidence.

### Phase 4: Auto-Write Draft Checks Immediately

1. Placement rules:
   - repo-wide patterns -> `.agents/checks/`
   - area-specific patterns -> `subdir/.agents/checks/`
2. File naming convention:
   - `NN-category-topic.md` (example: `10-security-auth-invariants.md`)
3. Include examples/non-examples where possible to reduce false positives.
4. Include a short rationale section with source PR references.

### Phase 5: Produce Review Report

1. Generate `artifacts/check-bootstrap-report.md` including:
   - each proposed check
   - linked PR evidence snippets
   - confidence score
   - estimated false-positive risk
   - recommendation: keep, refine, or drop

## Draft Check File Template

Each generated check draft should follow:

```md
---
name: security-auth-invariants
description: Ensure auth-sensitive routes enforce required invariants
severity-default: high
tools: [Grep, Read]
---

Look for:

- Missing auth/authorization guard in protected handlers
- Inconsistent permission checks across similar endpoints

Report:

- File and line
- Why this matters
- Suggested remediation

Rationale (derived from recent PRs):

- Repeated review comments in PR #123, #127, #131
```

## Skill Directory Layout

```text
bootstrap-checks-from-prs/
  SKILL.md
  scripts/
    collect_prs.py
    extract_rule_candidates.py
    generate_check_drafts.py
    write_checks.py
    generate_report.py
  references/
    taxonomy.md
    check-template.md
```

## Script Responsibilities (Python)

- `scripts/collect_prs.py`
  - Uses `gh` to fetch merged PRs and comments.
  - Writes normalized output to `artifacts/pr-scan.json`.
- `scripts/extract_rule_candidates.py`
  - Reads `artifacts/pr-scan.json`.
  - Clusters and scores candidate patterns.
  - Writes `artifacts/rule-candidates.json` (ranked, with scope + evidence pointers).
- `scripts/generate_check_drafts.py`
  - Renders top candidates (respecting `max_checks`) into markdown drafts.
  - Writes `artifacts/check-drafts.json` (filenames + content + metadata) for deterministic output.
- `scripts/write_checks.py`
  - Writes drafts into `.agents/checks/` and subtree folders.
  - Enforces collision policy (`-draft` suffix; never overwrite silently).
- `scripts/generate_report.py`
  - Writes `artifacts/check-bootstrap-report.md` and a concise console summary.

## `SKILL.md` Behavior Requirements

- Instruct the agent to:
  - gather the requested PR window,
  - infer candidate checks,
  - auto-write draft check files immediately,
  - then return a concise report for human review.
- Enforce safe defaults:
  - never overwrite existing check files silently,
  - if name collision occurs, write `-draft` suffix,
  - keep one check per file and keep checks focused.

## Quality Gates

- No check without repeated evidence (or strong security/compliance evidence)
- No check with unclear actionability (must include fix direction)
- No check that duplicates an existing lint rule unless the team policy is stricter
- Keep checks concise and stack-specific (avoid generic advice)
- Keep initial set small (respect `max_checks`)

## Risks and Mitigations

- Sparse PR data -> expand history window; label low-confidence suggestions
- Noisy comments -> require recurrence and cross-PR corroboration
- Overbroad checks -> split into smaller checks with explicit scope + preconditions
- Drift over time -> rerun bootstrap periodically and diff outputs

## Success Criteria

- Generates valid check files in expected format and correct directories
- Suggested checks map clearly to observed PR patterns (traceable evidence)
- Initial set is small and high-signal after one calibration pass
- Team can adopt with minimal editing

## Validation and Iteration Loop

- After initial generation, run a lightweight replay against a holdout PR set.
- Score each check for:
  - precision (noise level)
  - usefulness (actionability)
- Mark in report:
  - **Adopt now**
  - **Needs tuning**
  - **Drop**
- Re-run periodically (for example weekly) to keep checks aligned with current engineering patterns.

## Future Implementation Sequence

When implementation starts, do it in this order:

1. `SKILL.md` + invocation contract and defaults
2. `scripts/collect_prs.py` + normalized JSON output (`artifacts/pr-scan.json`)
3. `scripts/extract_rule_candidates.py` scoring/ranking (`artifacts/rule-candidates.json`)
4. `scripts/generate_check_drafts.py` markdown generation
5. `scripts/write_checks.py` filesystem writes with collision safety
6. `scripts/generate_report.py` report + calibration notes

## Deliverables

- A new skill: `bootstrap-checks-from-prs`
- Auto-written draft checks in `.agents/checks/` and relevant subtree check directories
- Evidence artifacts in `artifacts/` (`pr-scan.json`, `check-bootstrap-report.md`)
- A generated review report that helps maintainers quickly approve or refine drafts
