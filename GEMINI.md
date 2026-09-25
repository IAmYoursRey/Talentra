# TALENTRA.ID Workspace Instructions

Build TALENTRA.ID phase-by-phase. Preserve working code, keep diffs scoped, and do not jump ahead of the active phase.

## Operating rules
- Read `TALENTRA/state/phase-state.json` first when it exists.
- Read only the current phase section in `TALENTRA/PHASES.md` plus references required for the task.
- Search before reading whole files. Prefer targeted file/range reads.
- Delegate specialist work to the TALENTRA custom agents when useful.
- Do not invent existing APIs, schemas, files, environment variables, or completed features.
- UI phases may use typed mock adapters; backend phases must replace mocks behind stable interfaces instead of rewriting screens.
- Treat PostgreSQL as relational source-of-truth, MongoDB as dynamic evidence/document store, and object storage as blob storage.
- Authorization is server-enforced. Never trust a client-provided role.
- Never expose full NISN, NIP/NUPTK, NPSN, passwords, tokens, signed storage URLs, or private portfolio objects in logs/UI fixtures.
- Only teacher-approved portfolio evidence can affect skill visualizations, career recommendations, generated CVs, or public verification.
- Run relevant lint/typecheck/tests before marking a phase complete.
- Update `TALENTRA/state/phase-state.json` and write a concise phase summary after material changes.
- Advance to another phase only when the current phase acceptance criteria pass or the user explicitly overrides the gate.

## Quality
Prefer simple, testable modules and explicit contracts. Avoid speculative abstractions. Do not add dependencies when the existing stack already solves the problem.
