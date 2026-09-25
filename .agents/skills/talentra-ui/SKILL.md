---
name: talentra-ui
description: Build or revise TALENTRA's mobile-first Next.js/React PWA UI, role dashboards, forms, charts, states, and frontend service contracts. Use for Phase 1 and later frontend integration.
---

# UI procedure

1. Inspect existing app/router, component library, CSS/tokens, and package dependencies.
2. Define or reuse a small design system before duplicating feature-specific styling.
3. Implement role shells and routes from Phase 1.
4. Keep data access behind typed adapters; use mocks only through those adapters.
5. For each data view cover loading, empty, error, and success; add forbidden when role-sensitive.
6. Make charts responsive and provide a textual/accessible interpretation.
7. Ensure upload/tag/review controls work with keyboard and touch.
8. Add PWA manifest/icons/service-worker strategy consistent with the selected Next setup.
9. Run typecheck/lint/build and relevant component/E2E smoke checks.

Do not add real auth policy inside components. Components may hide controls for UX, but the backend remains authoritative.
