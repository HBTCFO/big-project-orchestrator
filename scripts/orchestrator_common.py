#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path


TEMPLATE_NAMES = [
    "new_requirements.md",
    "current_requirements.md",
    "todo.md",
    "decisions.md",
    "status.md",
    "handoff.md",
    "review.md",
    "verification.commands.sh",
    "setup.commands.sh",
]

SPEC_CANDIDATES = ["spec.md", "requirements.md", "task.md", "README.md"]


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def skill_dir() -> Path:
    return script_dir().parent


def templates_dir() -> Path:
    return skill_dir() / "assets" / "templates"


def orch_dir(repo: Path) -> Path:
    return repo / ".codex" / "orchestrator"


def state_path(repo: Path) -> Path:
    return orch_dir(repo) / "state.json"


def last_verification_path(repo: Path) -> Path:
    return orch_dir(repo) / "last_verification.json"


def last_review_path(repo: Path) -> Path:
    return orch_dir(repo) / "last_review.json"


def history_path(repo: Path) -> Path:
    return orch_dir(repo) / "planner_history.txt"


def tracks_dir(repo: Path) -> Path:
    return orch_dir(repo) / "tracks"


def tracks_manifest_path(repo: Path) -> Path:
    return orch_dir(repo) / "tracks.json"


def track_board_path(repo: Path) -> Path:
    return orch_dir(repo) / "track_board.md"


def dispatch_dir(repo: Path) -> Path:
    return orch_dir(repo) / "dispatch"


def dispatch_manifest_path(repo: Path) -> Path:
    return orch_dir(repo) / "dispatch.json"


def prompts_dir(repo: Path) -> Path:
    return orch_dir(repo) / "prompts"


def prompts_manifest_path(repo: Path) -> Path:
    return orch_dir(repo) / "prompts.json"


def track_readiness_path(repo: Path) -> Path:
    return orch_dir(repo) / "track_readiness.json"


def track_readiness_markdown_path(repo: Path) -> Path:
    return orch_dir(repo) / "track_readiness.md"


def convergence_dir(repo: Path) -> Path:
    return orch_dir(repo) / "convergence"


def convergence_manifest_path(repo: Path) -> Path:
    return orch_dir(repo) / "convergence.json"


def convergence_brief_path(repo: Path) -> Path:
    return orch_dir(repo) / "convergence.md"


def merge_report_path(repo: Path) -> Path:
    return orch_dir(repo) / "merge_report.json"


def merge_report_markdown_path(repo: Path) -> Path:
    return orch_dir(repo) / "merge_report.md"


def supervisor_report_path(repo: Path) -> Path:
    return orch_dir(repo) / "supervisor_report.json"


def supervisor_report_markdown_path(repo: Path) -> Path:
    return orch_dir(repo) / "supervisor_report.md"


def escalation_report_path(repo: Path) -> Path:
    return orch_dir(repo) / "escalation_report.json"


def escalation_report_markdown_path(repo: Path) -> Path:
    return orch_dir(repo) / "escalation_report.md"


def automation_report_path(repo: Path) -> Path:
    return orch_dir(repo) / "automation_report.json"


def automation_report_markdown_path(repo: Path) -> Path:
    return orch_dir(repo) / "automation_report.md"


def automation_pack_dir(repo: Path) -> Path:
    return orch_dir(repo) / "automation"


def automation_pack_manifest_path(repo: Path) -> Path:
    return orch_dir(repo) / "automation_pack.json"


def automation_pack_markdown_path(repo: Path) -> Path:
    return orch_dir(repo) / "automation_pack.md"


def automation_memory_path(repo: Path) -> Path:
    return orch_dir(repo) / "automation_memory.json"


def automation_memory_markdown_path(repo: Path) -> Path:
    return orch_dir(repo) / "automation_memory.md"


def execution_bridge_path(repo: Path) -> Path:
    return orch_dir(repo) / "execution_bridge.json"


def execution_bridge_markdown_path(repo: Path) -> Path:
    return orch_dir(repo) / "execution_bridge.md"


def orchestration_run_path(repo: Path) -> Path:
    return orch_dir(repo) / "orchestration_run.json"


def orchestration_run_markdown_path(repo: Path) -> Path:
    return orch_dir(repo) / "orchestration_run.md"


def validation_report_path(repo: Path) -> Path:
    return orch_dir(repo) / "validation_report.json"


def validation_report_markdown_path(repo: Path) -> Path:
    return orch_dir(repo) / "validation_report.md"


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def append_history(repo: Path, event: str) -> None:
    history = history_path(repo)
    history.parent.mkdir(parents=True, exist_ok=True)
    with history.open("a", encoding="utf-8") as handle:
        handle.write(f"{now_stamp()} {event}\n")


def ensure_workspace(repo: Path, force: bool = False) -> Path:
    orch = orch_dir(repo)
    orch.mkdir(parents=True, exist_ok=True)
    (orch / "completed").mkdir(parents=True, exist_ok=True)
    tracks_dir(repo).mkdir(parents=True, exist_ok=True)
    dispatch_dir(repo).mkdir(parents=True, exist_ok=True)
    prompts_dir(repo).mkdir(parents=True, exist_ok=True)
    convergence_dir(repo).mkdir(parents=True, exist_ok=True)
    automation_pack_dir(repo).mkdir(parents=True, exist_ok=True)
    for name in TEMPLATE_NAMES:
        src = templates_dir() / name
        dest = orch / name
        if force or not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    history = history_path(repo)
    if force or not history.exists():
        history.write_text("", encoding="utf-8")
    return orch


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def is_placeholder_verifier(path: Path) -> bool:
    if not path.exists():
        return True
    return "BIG_PROJECT_ORCHESTRATOR_PLACEHOLDER=1" in read_text(path)


def discover_input_spec(repo: Path, explicit: str | None = None) -> Path | None:
    if explicit:
        candidate = (repo / explicit).resolve()
        return candidate if candidate.exists() else None
    for name in SPEC_CANDIDATES:
        candidate = repo / name
        if candidate.exists():
            return candidate
    return None


def detect_project_mode(repo: Path, spec_text: str = "") -> str:
    markers = [
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "Makefile",
    ]
    if any((repo / marker).exists() for marker in markers):
        return "existing_repo"
    if any((repo / dirname).is_dir() for dirname in ["src", "app", "tests", "cmd"]):
        return "existing_repo"
    if spec_text.strip():
        return "greenfield"
    return "unknown"


def infer_stack(repo: Path, spec_text: str = "") -> dict[str, str]:
    lower = spec_text.lower()
    if (repo / "package.json").exists():
        return {"primary": "node", "reason": "package.json detected"}
    if (repo / "pyproject.toml").exists() or (repo / "requirements.txt").exists():
        return {"primary": "python", "reason": "Python project files detected"}
    if (repo / "Cargo.toml").exists():
        return {"primary": "rust", "reason": "Cargo.toml detected"}
    if (repo / "go.mod").exists():
        return {"primary": "go", "reason": "go.mod detected"}
    if (repo / "pom.xml").exists() or (repo / "build.gradle").exists() or (repo / "build.gradle.kts").exists():
        return {"primary": "java", "reason": "Java build files detected"}

    keyword_map = {
        "node": ["node", "typescript", "javascript", "react", "next.js", "nextjs", "express"],
        "python": ["python", "fastapi", "django", "flask", "pydantic"],
        "go": ["golang", "go service", "go api"],
        "rust": ["rust", "cargo"],
        "java": ["spring", "java", "gradle", "maven", "kotlin"],
    }
    for primary, keywords in keyword_map.items():
        if any(keyword in lower for keyword in keywords):
            return {"primary": primary, "reason": f"spec keywords matched {primary}"}

    return {"primary": "unknown", "reason": "No repository markers or reliable spec keywords detected"}


def _package_manager(repo: Path) -> str:
    if (repo / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (repo / "yarn.lock").exists():
        return "yarn"
    return "npm"


def default_verification_plan(repo: Path, spec_text: str = "", project_mode: str = "unknown") -> dict:
    stack = infer_stack(repo, spec_text)
    primary = stack["primary"]
    commands: list[str] = []
    strategy = "bundled"

    if (repo / "package.json").exists():
        try:
            package = json.loads(read_text(repo / "package.json"))
        except json.JSONDecodeError:
            package = {}
        scripts = package.get("scripts", {}) if isinstance(package.get("scripts"), dict) else {}
        pm = _package_manager(repo)
        for script_name in ["lint", "typecheck", "test", "build"]:
            if script_name in scripts:
                if pm == "yarn":
                    commands.append(f"yarn {script_name}")
                else:
                    commands.append(f"{pm} run {script_name}")
        if commands:
            strategy = "repo-native"
    elif (repo / "pyproject.toml").exists() or (repo / "requirements.txt").exists() or (repo / "main.py").exists():
        if (repo / "tests").exists():
            commands.append("python3 -m unittest discover -s tests -p 'test*.py'")
        commands.append("python3 -m compileall .")
        strategy = "repo-native"
    elif (repo / "Cargo.toml").exists():
        commands = ["cargo test --all", "cargo build --all-targets"]
        strategy = "repo-native"
    elif (repo / "go.mod").exists():
        commands = ["go test ./...", "go build ./..."]
        strategy = "repo-native"
    elif (repo / "pom.xml").exists():
        commands = ["./mvnw test" if (repo / "mvnw").exists() else "mvn test"]
        strategy = "repo-native"
    elif (repo / "gradlew").exists():
        commands = ["./gradlew test"]
        strategy = "repo-native"
    elif project_mode == "greenfield":
        strategy = "auto-generated"
        if primary == "python":
            commands = [
                "test -f pyproject.toml",
                "python3 -m unittest discover -s tests -p 'test*.py'",
                "python3 -m compileall src tests",
            ]
        elif primary == "node":
            commands = [
                "test -f package.json",
                "npm test",
                "npm run build",
            ]
        else:
            commands = [
                "test -f README.md",
                "test -d src",
                "test -d tests",
                "test -f .codex/orchestrator/current_requirements.md",
            ]

    return {
        "strategy": strategy,
        "stack": primary,
        "reason": stack["reason"],
        "commands": commands,
    }


def render_verification_script(commands: list[str], reason: str) -> str:
    body = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"# Generated by big-project-orchestrator: {reason}",
        "",
    ]
    body.extend(commands)
    body.append("")
    return "\n".join(body)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "milestone"


def sanitize_track_slug(value: str) -> str:
    return slugify(value)[:40]


def summarize_spec(spec_text: str, fallback: str = "Deliver the requested project with milestone-based execution.") -> str:
    lines = [line.strip() for line in spec_text.splitlines() if line.strip()]
    for line in lines:
        if line.startswith("#"):
            continue
        return line
    return fallback


def extract_bullets(spec_text: str) -> list[str]:
    bullets: list[str] = []
    for line in spec_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            bullets.append(stripped[2:].strip())
        elif re.match(r"^\d+\.\s+", stripped):
            bullets.append(re.sub(r"^\d+\.\s+", "", stripped))
    return bullets


def extract_headings(spec_text: str) -> list[str]:
    headings: list[str] = []
    for line in spec_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                headings.append(heading)
    return headings


def ensure_greenfield_structure(repo: Path, stack: str, goal: str) -> list[str]:
    created: list[str] = []

    def create(path: Path, content: str) -> None:
        if path.exists():
            return
        write_text(path, content)
        created.append(str(path.relative_to(repo)))

    create(
        repo / "README.md",
        f"# Project bootstrap\n\n## Goal\n\n{goal}\n\n## Status\n\nBootstrapped by big-project-orchestrator autonomous mode.\n",
    )
    (repo / "src").mkdir(exist_ok=True)
    (repo / "tests").mkdir(exist_ok=True)

    if stack == "python":
        create(
            repo / "pyproject.toml",
            "[project]\nname = \"autonomous-bootstrap\"\nversion = \"0.1.0\"\nrequires-python = \">=3.11\"\n",
        )
        create(repo / "src" / "__init__.py", "")
        create(
            repo / "src" / "main.py",
            "def main() -> None:\n    print(\"bootstrap ready\")\n\n\nif __name__ == \"__main__\":\n    main()\n",
        )
        create(
            repo / "tests" / "test_smoke.py",
            "import unittest\n\n\nclass SmokeTest(unittest.TestCase):\n    def test_bootstrap(self) -> None:\n        self.assertTrue(True)\n\n\nif __name__ == \"__main__\":\n    unittest.main()\n",
        )
    elif stack == "node":
        create(
            repo / "package.json",
            '{\n  "name": "autonomous-bootstrap",\n  "version": "0.1.0",\n  "private": true,\n  "scripts": {\n    "test": "node --test",\n    "build": "node -e \\"console.log(\'build ok\')\\""\n  }\n}\n',
        )
        create(repo / "src" / "index.js", "export function main() { return 'bootstrap ready'; }\n")
        create(
            repo / "tests" / "smoke.test.js",
            "const test = require('node:test');\nconst assert = require('node:assert/strict');\n\ntest('bootstrap', () => {\n  assert.equal(1, 1);\n});\n",
        )
    else:
        create(repo / "src" / ".gitkeep", "")
        create(repo / "tests" / ".gitkeep", "")

    return created


def append_decision(repo: Path, title: str, context: str, rationale: str, follow_up: str = "None.") -> None:
    path = orch_dir(repo) / "decisions.md"
    existing = read_text(path).rstrip()
    entry = (
        f"\n- {now_stamp()} — Decision: {title}\n"
        f"  - Context: {context}\n"
        f"  - Alternatives considered: Deferred manual selection.\n"
        f"  - Why this choice: {rationale}\n"
        f"  - Follow-up: {follow_up}\n"
    )
    write_text(path, (existing + entry + "\n").lstrip("\n"))
