from pathlib import Path
import re, sys, json

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors = []
warnings = []

required = [
    "GEMINI.md",
    "TALENTRA/BLUEPRINT.md",
    "TALENTRA/PHASES.md",
    "TALENTRA/state/phase-state.json",
    ".agents/agents/talentra-orchestrator/agent.md",
]
for rel in required:
    if not (ROOT / rel).exists():
        errors.append(f"missing required file: {rel}")

def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"missing YAML frontmatter: {path.relative_to(ROOT)}")
        return ""
    parts = text.split("---", 2)
    return parts[1] if len(parts) >= 3 else ""

for p in (ROOT / ".agents" / "agents").glob("**/agent.md"):
    fm = frontmatter(p)
    for key in ("name:", "description:"):
        if key not in fm:
            errors.append(f"{p.relative_to(ROOT)} missing {key[:-1]}")
    if "model: flash" not in fm:
        warnings.append(f"{p.relative_to(ROOT)} does not explicitly use flash tier")

for p in (ROOT / ".agents" / "skills").glob("*/SKILL.md"):
    fm = frontmatter(p)
    for key in ("name:", "description:"):
        if key not in fm:
            errors.append(f"{p.relative_to(ROOT)} missing {key[:-1]}")

for p in (ROOT / ".agents" / "rules").glob("*.md"):
    fm = frontmatter(p)
    if "trigger:" not in fm:
        errors.append(f"{p.relative_to(ROOT)} missing trigger")
    if len(p.read_text(encoding="utf-8")) > 12000:
        warnings.append(f"large rule file: {p.relative_to(ROOT)}")

state = ROOT / "TALENTRA/state/phase-state.json"
phases_file = ROOT / "TALENTRA/PHASES.md"
defined_phases = []
if phases_file.exists():
    defined_phases = [int(m) for m in re.findall(r"^## Phase (\d+)", phases_file.read_text(encoding="utf-8"), re.MULTILINE)]
if not defined_phases:
    defined_phases = list(range(1, 10))

if state.exists():
    try:
        obj = json.loads(state.read_text(encoding="utf-8"))
        active = obj.get("activePhase")
        status = obj.get("phaseStatus")
        completed = obj.get("completedPhases", [])

        # Check if caller specifically requested starter-kit validation
        if "--kit-starter" in sys.argv:
            if active != 1 or completed != []:
                warnings.append("initial activePhase is not 1 or completedPhases is not empty")
        else:
            # Semantic validation for project state:
            # 1. Fresh project: activePhase = 1, completed = []
            is_fresh = (active == 1 and len(completed) == 0)
            # 2. Completed project: completed = all defined phases, activePhase = null, phaseStatus = "complete"
            is_completed = (active is None and status == "complete" and completed == defined_phases)
            # 3. In-progress project: completed are sequential [1..k], activePhase = k + 1
            is_in_progress = (
                isinstance(active, int)
                and active in defined_phases
                and completed == [p for p in defined_phases if p < active]
            )

            if not (is_fresh or is_completed or is_in_progress):
                warnings.append(f"inconsistent phase state: activePhase={active}, status={status}, completedPhases={completed}")
    except Exception as exc:
        errors.append(f"invalid phase-state.json: {exc}")

print(json.dumps({
    "ok": not errors,
    "errors": errors,
    "warnings": warnings,
    "agents": len(list((ROOT / ".agents" / "agents").glob("**/agent.md"))),
    "skills": len(list((ROOT / ".agents" / "skills").glob("*/SKILL.md"))),
    "rules": len(list((ROOT / ".agents" / "rules").glob("*.md"))),
}, indent=2))
sys.exit(1 if errors else 0)
