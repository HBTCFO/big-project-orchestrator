#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from build_project_state import initialize_state
from orchestrator_common import (
    append_decision,
    append_history,
    default_verification_plan,
    extract_bullets,
    extract_headings,
    load_json,
    orch_dir,
    read_text,
    save_json,
    state_path,
    summarize_spec,
)


def _chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _derive_focus_areas(spec_text: str) -> list[str]:
    headings = [heading for heading in extract_headings(spec_text) if heading.lower() not in {"workflow", "overview"}]
    if headings:
        headings = headings[1:] if len(headings) > 1 else []
    if headings:
        return headings[:6]
    bullets = extract_bullets(spec_text)
    if bullets:
        return ["; ".join(chunk) for chunk in _chunked(bullets[:12], 3)]
    return []


def build_milestones(repo: Path, state: dict, max_milestones: int = 6) -> list[dict]:
    spec_path = repo / state["input_spec_path"] if state.get("input_spec_path") else None
    spec_text = read_text(spec_path) if spec_path else state.get("goal", "")
    plan = default_verification_plan(repo, spec_text, state.get("project_mode", "unknown"))
    focus_areas = _derive_focus_areas(spec_text)
    goal = summarize_spec(spec_text, state.get("goal", "Deliver the requested project."))

    milestones: list[dict] = []
    if state.get("project_mode") == "greenfield":
        milestones.append(
            {
                "id": "m1-foundation",
                "title": "Foundation bootstrap",
                "goal": "Create a runnable project skeleton, durable orchestrator state, and baseline verification.",
                "inputs": [state.get("input_spec_path") or "inline request"],
                "deliverables": [
                    "Baseline repo structure",
                    "Initial verification path",
                    "Current milestone artifacts",
                ],
                "acceptance_criteria": [
                    "Project has a minimal runnable skeleton",
                    "Verification can run locally without external APIs",
                    "Durable orchestrator files reflect the active plan",
                ],
                "validation_commands": plan["commands"],
                "risks": ["Chosen stack assumptions may need revisiting once implementation starts."],
                "done_when": [
                    "Bootstrap files exist",
                    "Verification passes or a concrete blocker is documented",
                ],
                "status": "planned",
            }
        )

    core_focus = focus_areas[: max(1, max_milestones - len(milestones) - 2)]
    for index, area in enumerate(core_focus, start=len(milestones) + 1):
        milestone_id = f"m{index}-{area.lower().replace(' ', '-')[:24].strip('-') or 'feature'}"
        milestones.append(
            {
                "id": milestone_id,
                "title": area[:80],
                "goal": f"Implement and validate the following project slice: {area}.",
                "inputs": [state.get("input_spec_path") or "inline request"],
                "deliverables": [area],
                "acceptance_criteria": [f"{area} is implemented and reflected in the repo state."],
                "validation_commands": plan["commands"],
                "risks": ["Scope may need narrowing if this area expands beyond a reviewable diff."],
                "done_when": ["Verification passes for the active implementation slice."],
                "status": "planned",
            }
        )

    milestones.append(
        {
            "id": f"m{len(milestones)+1}-hardening",
            "title": "Verification and hardening",
            "goal": "Close validation gaps, eliminate obvious regressions, and tighten the acceptance surface.",
            "inputs": [state.get("input_spec_path") or "inline request"],
            "deliverables": ["Passing verification", "Resolved high-priority defects", "Updated decisions/status"],
            "acceptance_criteria": ["Primary validation commands pass or documented blockers remain."],
            "validation_commands": plan["commands"],
            "risks": ["Late-stage issues may force earlier milestone changes."],
            "done_when": ["The project passes the agreed validation surface."],
            "status": "planned",
        }
    )
    milestones.append(
        {
            "id": f"m{len(milestones)+1}-handoff",
            "title": "Handoff and release notes",
            "goal": "Leave the project in a reviewable, resumable, and release-ready state.",
            "inputs": [state.get("input_spec_path") or "inline request"],
            "deliverables": ["Current status", "Decision log", "Handoff notes"],
            "acceptance_criteria": ["A new thread can resume work using only orchestrator artifacts."],
            "validation_commands": [],
            "risks": ["Docs drift if implementation changes are not reflected immediately."],
            "done_when": ["handoff.md and status.md are current and actionable."],
            "status": "planned",
        }
    )

    return milestones[:max_milestones]


def _render_new_requirements(state: dict, milestones: list[dict]) -> str:
    deliverables = [deliverable for milestone in milestones for deliverable in milestone["deliverables"][:2]]
    criteria = [criterion for milestone in milestones for criterion in milestone["acceptance_criteria"][:1]]
    return (
        "# New requirements\n\n"
        f"## User goal\n\n{state['goal']}\n\n"
        "## Scope\n\n"
        "- In scope: Execute the project milestone by milestone using local Codex workflows.\n"
        "- Out of scope: External APIs, non-local automation, and unrelated refactors.\n\n"
        "## Constraints\n\n"
        "- Platform(s): Local machine only.\n"
        f"- Stack constraints: Prefer {state['stack']['primary']} unless the repo proves otherwise.\n"
        "- Performance / security / UX constraints: Keep decisions explicit and validation repeatable.\n"
        "- Files or subsystems to avoid touching: Anything outside the active milestone.\n\n"
        "## Deliverables\n\n"
        + "".join(f"- {item}\n" for item in deliverables[:8])
        + "\n## Acceptance criteria\n\n"
        + "".join(f"- [ ] {item}\n" for item in criteria[:8])
        + "\n## Validation commands\n\n```bash\n# See current_requirements.md for the active milestone command set.\n```\n\n"
        "## Open questions\n\n- [ ] Are the inferred stack and milestone boundaries still correct after milestone 1?\n"
    )


def render_current_milestone(milestone: dict) -> str:
    commands = "\n".join(milestone["validation_commands"]) or "# Add project-specific validation commands here."
    return (
        "# Current milestone\n\n"
        f"## Milestone title\n\n{milestone['title']}\n\n"
        f"## Goal\n\n{milestone['goal']}\n\n"
        "## Scope\n\n"
        + "".join(f"- In scope: {item}\n" for item in milestone["deliverables"])
        + "- Out of scope: Future milestones and unrelated cleanup.\n\n"
        "## Acceptance criteria\n\n"
        + "".join(f"- [ ] {item}\n" for item in milestone["acceptance_criteria"])
        + "\n## Validation commands\n\n```bash\n"
        + commands
        + "\n```\n\n## Done when\n\n"
        + "".join(f"- [ ] {item}\n" for item in milestone["done_when"])
    )


def render_todo(milestone: dict) -> str:
    tasks = [
        "Freeze the acceptance criteria for this milestone",
        *milestone["deliverables"],
        "Run verification",
        "Update status, handoff, and decisions",
        "Archive the milestone when complete",
    ]
    return "# Active milestone checklist\n\n" + "".join(f"- [ ] {task}\n" for task in tasks)


def activate_milestone_files(repo: Path, state: dict, milestone: dict) -> None:
    orch = orch_dir(repo)
    (orch / "current_requirements.md").write_text(render_current_milestone(milestone), encoding="utf-8")
    (orch / "todo.md").write_text(render_todo(milestone), encoding="utf-8")
    (orch / "status.md").write_text(
        "# Status\n\n## Current state\n\n"
        "- Phase: implement\n"
        "- Branch / thread: current thread\n"
        "- Working mode: Local\n"
        f"- Active milestone: {milestone['title']}\n"
        f"- Last verification result: {state.get('verification', {}).get('status', 'not_run')}\n"
        f"- Last review result: {state.get('review', {}).get('status', 'not_run')}\n"
        "- Primary blocker: none\n\n"
        "## Completed in this cycle\n\n- [ ] Previous milestone archived\n\n"
        "## In progress\n\n"
        f"- [ ] {milestone['title']}\n\n"
        "## Verification summary\n\n- Strategy:\n- Commands run:\n- Failures:\n\n"
        "## Review summary\n\n- Status:\n- Findings:\n- Blocking findings:\n\n"
        "## Repair loop\n\n- Attempts:\n- Last repair action:\n\n"
        "## Next best action\n\n"
        f"- [ ] Implement {milestone['title']}\n",
        encoding="utf-8",
    )
    (orch / "handoff.md").write_text(
        "# Handoff\n\n## What changed\n\n- Advanced to the next active milestone.\n\n"
        "## What still needs work\n\n"
        f"- {milestone['goal']}\n\n"
        "## Exact next step\n\n1. Implement the active milestone and rerun autonomous verification.\n\n"
        "## Current phase\n\n- implement\n\n"
        f"## Active milestone\n\n- Title: {milestone['title']}\n- Done when: {milestone['done_when'][0]}\n\n"
        "## Commands to run next\n\n```bash\npython3 <skill-dir>/scripts/run_autonomous_cycle.py --repo \"$PWD\" --resume\n```\n\n"
        "## Risks / gotchas\n\n- [ ] Re-check scope if the milestone stops being reviewable.\n",
        encoding="utf-8",
    )


def generate_milestones(repo: Path, max_milestones: int = 6) -> dict:
    state = initialize_state(repo)
    milestones = build_milestones(repo, state, max_milestones=max_milestones)
    if not milestones:
        raise SystemExit("Unable to derive milestones from the current spec.")

    milestones[0]["status"] = "active"
    state["milestones"] = milestones
    state["current_milestone_id"] = milestones[0]["id"]
    state["active_tasks"] = milestones[0]["deliverables"]
    state["current_phase"] = "implement"
    state["next_action"] = "implement"
    save_json(state_path(repo), state)

    orch = orch_dir(repo)
    (orch / "new_requirements.md").write_text(_render_new_requirements(state, milestones), encoding="utf-8")
    activate_milestone_files(repo, state, milestones[0])

    append_history(repo, f"generate_milestones count={len(milestones)} active={milestones[0]['id']}")
    append_decision(
        repo,
        "Generate milestone plan",
        f"Goal={state['goal']}",
        f"Created {len(milestones)} milestones and activated {milestones[0]['id']}.",
        "Re-split the plan only if a milestone stops being reviewable.",
    )
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a milestone plan from the current spec")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--max-milestones", type=int, default=6, help="Maximum milestone count")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    state = generate_milestones(repo, max_milestones=args.max_milestones)
    print(state["current_milestone_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
