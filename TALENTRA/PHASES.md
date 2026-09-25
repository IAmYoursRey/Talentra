# TALENTRA.ID Development Phases

Do one phase at a time. A phase is complete only when its acceptance checks pass.

## Phase 1 — UI foundation + PWA shell
Goal: build the complete navigational experience with typed mock data before backend coupling.

Deliver:
- Design tokens, typography, spacing, responsive layout, accessible components.
- Mobile-first PWA shell, manifest, installability baseline, offline/fallback strategy.
- `/login`.
- Student: `/student`, `/student/portfolio/new`, `/student/skills`, `/student/cv`.
- Teacher: `/teacher`, `/teacher/reviews`, `/teacher/reviews/[id]`.
- Admin: `/admin`, `/admin/users`, `/admin/classes`.
- Public: `/verify/[token]`.
- Role-specific navigation and realistic empty/loading/error/success states.
- Mock adapters/interfaces for auth, portfolio, reviews, analytics, recommendations, CV.

Acceptance:
- Responsive at common phone/tablet/desktop widths.
- Keyboard navigation and accessible labels for key flows.
- No production credentials or backend dependency.
- Every planned route renders without runtime error.
- UI is built around stable typed contracts, not scattered hard-coded objects.

## Phase 2 — Auth + routing + RBAC
Goal: connect login identity to secure server-side role routing.

Deliver:
- User role enum: `student | teacher | admin`.
- Credential adapters for NISN; NIP/NUPTK/teacher SSO; school admin identity.
- Password change/recovery architecture.
- JWT session flow; secure cookie/token handling according to selected architecture.
- Server guards/middleware and endpoint policy checks.
- Post-login canonical redirect by role.
- 401/403 behavior and audit events.

Acceptance:
- A client cannot become another role by editing local state.
- Cross-role route/API attempts are denied server-side.
- Session expiration/logout work.
- Tests cover allowed/forbidden matrices.

## Phase 3 — Data + API + storage foundation
Goal: make persistence and API contracts real without yet implementing every feature.

Deliver:
- PostgreSQL relational schema/migrations.
- MongoDB collections/indexes for dynamic portfolio evidence.
- Private object-storage upload/download abstraction.
- Stable UUIDs across stores; no cross-database assumption of ACID.
- API DTO validation and typed client contracts.
- Dev seed with synthetic identities only.
- Health checks and structured error envelope.

Acceptance:
- Migrations are reproducible.
- Seed/reset is safe in development only.
- Upload authorization and size/type policies exist.
- No secrets committed.

## Phase 4 — Student proof-of-work workflow
Goal: complete evidence submission.

Deliver:
- Draft/create/edit/submit flows.
- PDF/JPG/MP4 and URL evidence.
- Mandatory 3–5 canonical tags.
- Ownership checks.
- Evidence status timeline.
- Resubmission after revision.
- File metadata and object references; no blob in database.

Acceptance:
- Invalid tag count/type/file rejected.
- Student can mutate only own eligible draft/revision submissions.
- Submitted evidence is immutable except through an explicit revision path.
- Audit trail preserved.

## Phase 5 — Teacher validation + scoring
Goal: turn evidence into trusted skill signals.

Deliver:
- Approval queue scoped to teacher assignment.
- Endorse / revise / reject, each with recorded actor/time/reason where required.
- Soft-skill rubric sliders 1–5 with rubric definitions.
- Approved-evidence projection.
- Student radar chart driven only by eligible validated evidence.

Acceptance:
- A teacher cannot validate out-of-scope students.
- Rejected/pending evidence contributes zero to published score.
- Score computation is deterministic and tested.
- Decision history is append-only or equivalently auditable.

## Phase 6 — Admin + school analytics
Goal: school-level operations and talent visibility.

Deliver:
- User/class/teacher-assignment CRUD with safeguards.
- Password reset/recovery administration without revealing passwords.
- Aggregate talent heatmap.
- Cohort/time filters with minimum-group privacy threshold.
- Audit log for sensitive admin actions.

Acceptance:
- Analytics uses validated data.
- Small-group privacy rule prevents accidental singling-out.
- Destructive actions require explicit confirmation and authorization.

## Phase 7 — Recommendation engine + industry translator
Goal: explainable longitudinal guidance.

Deliver:
- Skill evidence aggregation across semesters/years.
- Versioned mapping from skill/tag clusters to study/career families.
- Confidence/evidence summary; configurable weights.
- Recommendation output with "why this appears".
- Industry-language rewrite service with factuality constraints.

Acceptance:
- Same evidence/config => deterministic score/rank before any prose generation.
- Every recommendation links to contributing evidence categories.
- Protected traits are absent from scoring.
- Translator cannot invent ungrounded achievements.

## Phase 8 — Digital CV + QR verification
Goal: produce a verifiable public artifact.

Deliver:
- CV generated only from approved evidence.
- Stable PDF layout.
- Opaque, revocable, signed/random verification token.
- Public `/verify/[token]` page with minimal data.
- Verification record version/revocation support.

Acceptance:
- Guessing a student ID cannot reveal a CV.
- Revoked/expired verification is visibly invalid.
- QR resolves on mobile.
- Public payload has no unnecessary identifiers.

## Phase 9 — Integration + hardening + release
Goal: production readiness.

Deliver:
- End-to-end critical-flow tests.
- Security review, rate limits, validation, CSRF/XSS/injection checks as applicable.
- Observability without sensitive data leakage.
- Backup/restore notes.
- CI checks.
- Deployment configuration and rollback plan.
- Performance/PWA audit.

Acceptance:
- Critical E2E paths pass for all roles.
- No known critical/high security defect.
- Production env is separate from dev seed.
- Release checklist is documented.
