# Agent handoff contract

A worker should return a compact handoff instead of a long narrative.

Use this shape conceptually:

```json
{
  "phase": 1,
  "task": "student dashboard shell",
  "status": "done|partial|blocked",
  "changedFiles": ["..."],
  "contractsChanged": ["..."],
  "checks": [{"name":"typecheck","result":"pass"}],
  "risks": ["..."],
  "next": ["..."]
}
```

Rules:
- Do not paste source code into the handoff.
- Do not restate the full blueprint.
- Maximize paths, decisions, test results, and unresolved risks.
- If blocked, state the exact missing dependency.
- If a contract changed, point to the canonical file that defines it.
