---
trigger: model_decision
description: Apply when changing authentication, authorization, uploads, public verification, sensitive student data, admin actions, tokens, passwords, or storage.
---
Before editing, read `TALENTRA/references/security-privacy.md`.

For every sensitive endpoint/action verify: identity -> role -> tenant/school -> ownership/assignment -> state -> input policy.

Security behavior must be covered by negative tests, not only happy paths.
