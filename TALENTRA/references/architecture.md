# Architecture reference

## Preferred deployment shape

```text
Next.js PWA
   |
   | HTTPS
   v
API / application services
   |---------- PostgreSQL: identity, school/class relationships, validation ledger
   |---------- MongoDB: portfolio/evidence document metadata, dynamic tag payloads
   |---------- Object storage: PDF/JPG/MP4 private blobs
   |---------- Queue/outbox (when needed): projections, CV generation, async media work
```

FastAPI is preferred for the API/recommendation service because the scoring logic is naturally expressed in Python, but the architecture allows Node/Express if the project explicitly chooses it.

## Source-of-truth boundaries

### PostgreSQL
Suggested relational entities:
- `schools`
- `users`
- `student_profiles`
- `teacher_profiles`
- `classes`
- `enrollments`
- `teacher_assignments`
- `auth_identities`
- `sessions` or refresh-token records
- `validation_decisions`
- `rubric_assessments`
- `audit_events`
- `verification_records`
- optional materialized `student_skill_scores`

### MongoDB
Suggested collections:
- `portfolio_items`
- `portfolio_revisions`
- `evidence_tag_snapshots`
- `recommendation_snapshots`
- optional `cv_content_snapshots`

Every document uses an application UUID referencing a relational identity/entity; do not join by official national identifier.

### Object storage
Private-by-default keys such as:
`schools/<school_uuid>/students/<student_uuid>/portfolio/<item_uuid>/<object_uuid>`

Never use NISN/NIP/NPSN as an object key exposed to clients.

## Cross-store consistency
Do not pretend PostgreSQL + MongoDB + object storage share a transaction.
Use:
- idempotency keys,
- explicit state transitions,
- outbox/event processing when asynchronous projections are introduced,
- compensating cleanup for failed uploads,
- reconciliation jobs for orphan metadata/objects.

## API principles
- Server validates identity, role, ownership, assignment scope, state transition, and input schema.
- Client role is presentation context, never authority.
- Return stable error codes plus safe messages.
- Cursor pagination for large queues/portfolio lists.
- Public verification endpoint returns a deliberately small DTO.
