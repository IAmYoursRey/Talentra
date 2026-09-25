---
name: talentra-portfolio
description: Implement TALENTRA proof-of-work submission, 3–5 canonical tags, revision state machine, teacher validation queue, rubric scoring, and approved-evidence projection.
---

# Portfolio + validation procedure

1. Read `TALENTRA/references/domain-model.md`.
2. Enforce the portfolio state machine on the server.
3. Require 3–5 canonical tags on submit.
4. Validate file/link inputs and ownership.
5. Store file object metadata, not binary content, in the database.
6. Teacher queue must be scoped by school and assignment.
7. Validation decisions are attributable and auditable.
8. Approved-evidence projection is the only input to published radar/CV/recommendation pipelines.
9. Revision creates/preserves history rather than rewriting the previous accepted/rejected decision.
10. Tests must include invalid transitions, cross-student access, cross-teacher scope, and pending/rejected zero-contribution behavior.
