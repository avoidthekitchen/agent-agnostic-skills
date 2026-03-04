# Taxonomy for Bootstrap Checks

Use these categories when clustering PR review signals into candidate checks.

## Categories

- `security invariants`
  - Authn/authz requirements
  - Secret handling
  - Input validation and injection risks
- `compliance requirements`
  - PII handling and logging hygiene
  - Auditability requirements
- `performance best practices`
  - N+1 or repeated expensive work
  - Missing pagination or batching
- `migration/deprecation reminders`
  - Deprecated APIs and old code paths
- `style conventions outside linters`
  - Team conventions that linters do not enforce
- `known team anti-patterns`
  - Repeated issues identified in review feedback

## Scoring Dimensions

Each candidate should be scored by:

1. `frequency`: how many distinct PRs include corroborating evidence
2. `severity/risk`: impact if not enforced
3. `detectability`: likelihood the check can reliably find issues
4. `scope`: repo-wide vs subtree-specific applicability

## Promotion Rules

- Promote when frequency reaches `min_frequency`.
- Allow lower-frequency promotion for strong security/compliance evidence.
- Prefer precision over breadth in initial output.

## Quality Gates

- No candidate without traceable PR evidence.
- No candidate without clear remediation direction.
- Avoid checks that duplicate existing lint rules unless policy is stricter.
- Keep checks concise, stack-specific, and scoped.
