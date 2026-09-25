# TALENTRA.ID Product Blueprint

## Product mission
TALENTRA.ID is a smart digital student portfolio that supplements or replaces a purely conventional report-card view with validated **proof of work**, longitudinal skill evidence, and explainable study/career recommendations.

## Roles

### Student
Official login identifier: NISN (10 digits) in the intended Indonesian school deployment.

Capabilities:
- Upload PDF/JPG/MP4 evidence or submit external links such as GitHub/Drive.
- Choose 3–5 capability tags for every submission.
- Track status: draft/submitted/revision/approved/rejected.
- See a radar chart derived only from approved evidence and eligible teacher scoring.
- Generate a professional digital CV from approved records.
- See explainable study/career suggestions near the end of school.

### Teacher / Validator
Login identity may use NUPTK/NIP or configured teacher SSO.

Capabilities:
- Approval queue.
- Endorse, request revision, or reject with reason.
- Assess selected soft skills on a 1–5 rubric.
- See only students/classes within authorized assignment scope.

### School Admin
Institution account anchored to the school identity (NPSN in the intended deployment).

Capabilities:
- School-level talent heatmap and aggregate trends.
- User, teacher assignment, class/rombel, enrollment, and reset/recovery administration.
- No silent ability to forge teacher validation history.

## Killer features

### Explainable recommendation engine
Aggregate evidence over multiple semesters/years. Every recommendation must be traceable to:
- approved artifacts/tags,
- teacher rubric observations,
- recency/consistency rules,
- transparent mapping from skill clusters to study/career families.

Do not use protected attributes. Do not present recommendations as deterministic outcomes.

### QR authenticity verification
Generated CV contains a unique opaque QR token. Scanning opens a public verification page that confirms selected signed facts from the school-backed record without exposing private student data.

### Industry-language translator
Convert school activity descriptions into professional competency language while preserving facts. It may improve wording, never invent responsibilities, metrics, tools, awards, or impact.

## Core invariants
1. Unapproved evidence never affects CV, radar chart, recommendations, or public verification.
2. Every validation decision is attributable and timestamped.
3. Public verification uses an opaque token, not NISN/NIP/NPSN.
4. File access is private-by-default.
5. Role checks and ownership checks are enforced in backend code.
6. Recommendations remain explainable and auditable.
