# TALENTRA.ID — Antigravity Agent Kit

Workspace-native agent + skill pack for building TALENTRA.ID with Google Antigravity and Gemini 3.8 Flash.

## What this kit is

This is not the TALENTRA application itself. It is the development control layer that tells Antigravity how to build the application in phases without repeatedly loading the whole repository.

The design follows five ideas adapted from the architecture of **Egonex-AI/Understand-Anything**:

1. Separate deterministic work from LLM judgment.
2. Split large work into specialist agents with narrow responsibilities.
3. Use explicit phase contracts and structured handoffs.
4. Validate outputs before advancing.
5. Load context progressively and incrementally to reduce token use.

## Native Antigravity layout

Antigravity discovers:

- Workspace agents: `.agents/agents/<name>/agent.md`
- Workspace skills: `.agents/skills/<name>/SKILL.md`
- Workspace rules: `.agents/rules/*.md`
- Always-on workspace instructions: `GEMINI.md`

The main agent in this kit is `talentra-orchestrator`.

## Install

### Simplest
Extract this ZIP into the root of the TALENTRA.ID repository so these paths exist:

```text
<repo>/
  GEMINI.md
  .agents/
  TALENTRA/
```

Then reopen Antigravity and select `talentra-orchestrator` from the Agents panel.

### PowerShell
From this extracted folder:

```powershell
.\install.ps1 C:\path\to\talentra
```

### Bash
```bash
./install.sh /path/to/talentra
```

The installers do not delete project files. Existing files with the same names are backed up with a timestamp.

## Recommended first prompt

Paste the contents of `TALENTRA/START_PROMPT.md`, or simply say:

> Build TALENTRA.ID using the TALENTRA phase system. Start with Phase 1 only. Do not implement backend logic yet. Finish the UI shell, responsive PWA experience, role-specific mock dashboards, and Phase 1 acceptance checks before asking to advance.

## Phase order

1. UI foundation and PWA shell
2. Authentication, role routing, and RBAC
3. Data model, API contracts, databases, and object storage
4. Student proof-of-work workflow
5. Teacher validation and skill scoring
6. Admin analytics and user management
7. Career recommendation and industry-language translation
8. Digital CV and QR verification
9. Integration, security hardening, tests, observability, deployment

The detailed gates are in `TALENTRA/PHASES.md`.

## Token-efficiency model

- `GEMINI.md` is intentionally small.
- Rules are activated by scope/need rather than one giant prompt.
- Skills contain task-specific procedures and are loaded only when relevant.
- Workers receive a bounded task, relevant file paths, acceptance criteria, and a compact handoff object.
- The current phase is persisted in `TALENTRA/state/phase-state.json`.
- Agents should search/grep before opening large files.
- Agents must not dump the whole repository into context.
- After a phase is completed, future work should read the phase summary rather than reconstructing history from chat.

## Default technical direction

The kit treats the following as the preferred baseline unless the project owner overrides it:

- Frontend: Next.js + React + TypeScript, mobile-first PWA
- Backend: FastAPI preferred for the scoring/recommendation service; an equivalent Node/Express implementation is allowed if deliberately chosen in the architecture decision
- Relational data: PostgreSQL
- Dynamic portfolio/evidence metadata: MongoDB
- Binary storage: S3-compatible object storage
- Authentication: JWT-based session architecture with server-enforced RBAC
- Charts: client chart library selected during UI phase
- PDF: server-generated or deterministic service-generated CV
- QR: opaque signed verification token, never a raw student identifier

## Important product rule

Career recommendations are advisory evidence summaries, not decisions. They must be explainable, editable by product policy, and based on validated portfolio evidence and teacher rubric data—not protected traits or hidden profiling.

## Research basis

See `TALENTRA/RESEARCH_NOTES.md`.
