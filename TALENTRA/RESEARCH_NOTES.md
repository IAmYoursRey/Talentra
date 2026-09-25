# Research notes — 25 Sep 2026

## Google Antigravity / Gemini
Official sources consulted:
- https://ai.google.dev/gemini-api/docs/antigravity-agent
- https://ai.google.dev/gemini-api/docs/latest-model
- https://www.antigravity.google/docs/agent
- https://www.antigravity.google/docs/skills
- https://www.antigravity.google/docs/rules
- https://www.antigravity.google/docs/subagents
- https://www.antigravity.google/docs/cli/commands/agents
- https://www.antigravity.google/docs/migration/workflows-to-skills/
- https://www.antigravity.google/changelog

Relevant current behavior:
- Gemini 3.8 Flash is the default Antigravity managed-agent model and is designed for long-horizon software engineering and agentic work.
- Custom workspace agents are discovered under `.agents/agents/`.
- Agent Skills are directory bundles containing `SKILL.md` and are progressively loaded based on description/relevance.
- Workspace rules can live in `GEMINI.md`, `AGENTS.md`, or `.agents/rules/*.md`.
- Custom subagents can be declared in Markdown with YAML frontmatter.
- Antigravity supports subagent delegation and isolated context.
- Workflows are being deprecated in favor of Skills; this kit therefore uses Skills, not new workflow files.

## Reference repository
Studied:
- https://github.com/Egonex-AI/Understand-Anything

Patterns intentionally reused:
- deterministic processing before semantic LLM work,
- narrow specialized agents,
- explicit phase boundaries,
- batch/scoped processing instead of repeatedly reading everything,
- validation/reviewer stage,
- persisted machine-readable intermediate state,
- partial-failure visibility,
- incremental updates.

No source code from Understand-Anything is embedded in this kit.
