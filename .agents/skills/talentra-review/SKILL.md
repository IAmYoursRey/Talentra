---
name: talentra-review
description: Validate a TALENTRA phase against its acceptance criteria, core invariants, security/privacy rules, tests, and regressions before phase completion.
---

# Review procedure

1. Resolve active phase and acceptance criteria.
2. Inspect the actual diff and changed contracts.
3. Run available lint/typecheck/tests/build relevant to touched code.
4. Check core invariants:
   - only approved evidence affects published outputs,
   - server-enforced role/tenant/scope checks,
   - validation/admin history remains auditable,
   - public verification exposes minimal data,
   - recommendation logic is grounded/explainable.
5. If sensitive behavior changed, read `TALENTRA/references/security-privacy.md`.
6. Search for secrets and accidental official-identifier logging in changed code.
7. Test at least one forbidden/invalid case for every new sensitive happy path.
8. Report:
   - `blocking`: must fix before phase close,
   - `warnings`: non-blocking risks,
   - `checks`: commands/tests and outcomes,
   - `verdict`: approve only when blocking is empty.

Do not mark acceptance criteria passed from code inspection alone when an executable check is available.
