---
name: talentra-data-api
description: Design and implement TALENTRA PostgreSQL, MongoDB, object-storage boundaries, migrations, API DTOs, and cross-store consistency. Use in Phase 3 or when changing persistence contracts.
---

# Data/API procedure

Read:
- `TALENTRA/references/architecture.md`
- `TALENTRA/references/domain-model.md`

Then:
1. Inventory existing schema/models and migration tool.
2. Define UUID-based cross-store identifiers.
3. Put relational identity/authorization/audit facts in PostgreSQL.
4. Put dynamic evidence/recommendation snapshots in MongoDB where appropriate.
5. Put blobs only in object storage.
6. Define indexes before high-volume queue/analytics features.
7. Make cross-store writes idempotent; document failure/compensation behavior.
8. Validate request/response DTOs.
9. Seed development with synthetic data only.
10. Test migrations and rollback/forward behavior supported by the chosen tool.

Avoid leaking database-specific shapes directly into UI contracts.
