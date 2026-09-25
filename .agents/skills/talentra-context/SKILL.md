---
name: talentra-context
description: Load only the minimum TALENTRA project context needed for a task. Use at the start of implementation, review, debugging, or when resuming work.
---

# Context protocol

1. Read `TALENTRA/state/phase-state.json`.
2. Read `GEMINI.md`.
3. Read only the active phase section from `TALENTRA/PHASES.md`.
4. Search for relevant existing files/contracts before opening whole directories.
5. Read a reference under `TALENTRA/references/` only when the task requires it.
6. Inspect changed files / version-control diff before assuming repository state.
7. If a prior phase summary exists, use it instead of reconstructing history from chat.

Do not:
- dump the whole repository,
- reread large lockfiles/generated files,
- load every skill,
- infer that a file/endpoint exists without verifying it.

For large modules, inspect symbols/grep results first, then read targeted ranges.
