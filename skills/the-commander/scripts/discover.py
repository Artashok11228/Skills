#!/usr/bin/env python3
"""Read-only inventory of local agent skills for Claude Code, Codex and Cursor.

Prints one UTF-8 JSON document to stdout. It never writes files and never uses
the network. The only external process it may start is a tool's own plugin
listing command from references/locations.json (disable with
--no-plugin-commands). Requires Python 3.8+ and the standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_FILE = "SKILL.md"
SKIP_DIRS = {".git", "node_modules"}
FRONTMATTER_MAX_LINES = 300
SELF_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOCATIONS = SELF_DIR / "references" / "locations.json"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KEY_LINE = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(?:\s+(.*)|\s*)$")


def current_os() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def path_key(path) -> str:
    """Identity used for de-duplication: resolved target, case-insensitive."""
    try:
        resolved = os.path.realpath(str(path))
    except OSError:
        resolved = os.path.abspath(str(path))
    return os.path.normcase(resolved).casefold()


def display_path(path) -> str:
    return str(path).replace("\\", "/")


# ---------------------------------------------------------------- frontmatter

def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except ValueError:
            return value[1:-1]
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def parse_frontmatter(lines):
    """Parse the simple YAML subset used by SKILL.md frontmatter.

    Returns (fields, error). Only top-level keys are kept; nested mappings and
    lists are stored as flattened text, which is enough for name/description.
    """
    if not lines or lines[0].strip() != "---":
        return None, "missing frontmatter: file must start with ---"
    end = next((i for i in range(1, len(lines)) if lines[i].strip() in ("---", "...")), None)
    if end is None:
        return None, "unterminated frontmatter: closing --- not found"

    fields = {}
    key, style, parts = None, "plain", []

    def finish():
        if key is None:
            return
        if style == "literal":
            text = "\n".join(parts).strip()
        else:
            text = " ".join(part.strip() for part in parts if part.strip())
        fields[key] = text if style in ("literal", "folded") else unquote(text)

    for number, raw in enumerate(lines[1:end], start=2):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            if style == "literal" and key is not None:
                parts.append("")
            continue
        indented = line[0] in " \t"
        match = None if indented else KEY_LINE.match(line)
        if match:
            finish()
            key, rest = match.group(1), (match.group(2) or "").strip()
            if rest[:1] in ("|", ">") and re.fullmatch(r"[|>][+-]?\d*", rest):
                style, parts = ("literal" if rest[0] == "|" else "folded"), []
            else:
                style, parts = "plain", [rest]
        elif key is not None and (indented or line.startswith("- ")):
            parts.append(line.strip() if style != "literal" else line.strip())
        else:
            return None, "unparseable frontmatter line %d: %r" % (number, line[:80])
    finish()
    return fields, None


def read_frontmatter(skill_file: Path):
    """Read only the frontmatter block, never the body."""
    lines = []
    try:
        with open(skill_file, "r", encoding="utf-8-sig", errors="strict") as handle:
            for index, line in enumerate(handle):
                lines.append(line.rstrip("\r\n"))
                if index > 0 and line.strip() in ("---", "..."):
                    break
                if index >= FRONTMATTER_MAX_LINES:
                    break
    except UnicodeDecodeError:
        return None, "not valid UTF-8"
    except OSError as error:
        return None, "unreadable: %s" % error.strerror
    return parse_frontmatter(lines)


def is_true(value) -> bool:
    return str(value).strip().lower() in ("true", "yes", "1")


def codex_implicit_policy(skill_dir: Path):
    """agents/openai.yaml policy.allow_implicit_invocation, read with a regex."""
    meta = skill_dir / "agents" / "openai.yaml"
    try:
        text = meta.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None, []
    implicit = None
    match = re.search(r"allow_implicit_invocation\s*:\s*(\w+)", text)
    if match:
        implicit = is_true(match.group(1))
    hints = re.findall(r"type\s*:\s*[\"']?(\w+)[\"']?\s*\n\s*value\s*:\s*[\"']?([^\"'\n]+)", text)
    return implicit, ["%s:%s" % (kind, value.strip()) for kind, value in hints]


# ------------------------------------------------------------------ scanning

def resolve_bases(entry, home: Path, project_dirs, system_root):
    base = entry["base"]
    if base == "home":
        return [home / entry["path"]]
    if base == "project":
        return [directory / entry["path"] for directory in project_dirs]
    if base == "absolute":
        if system_root is None:
            return [Path(entry["path"])]
        relative = re.sub(r"^([A-Za-z]):", r"\1", entry["path"]).lstrip("/\\")
        return [system_root / relative]
    raise ValueError("unknown base %r" % base)


def find_skill_dirs(root: Path, max_depth: int, skip_children, report):
    found, stack, visited = [], [(root, 0)], set()
    while stack:
        directory, depth = stack.pop()
        identity = path_key(directory)
        if identity in visited:
            continue
        visited.add(identity)
        if depth >= 1 and (directory / SKILL_FILE).is_file():
            found.append(directory)
            continue
        if depth >= max_depth:
            continue
        try:
            entries = list(os.scandir(directory))
        except PermissionError:
            report["errors"].append({"path": display_path(directory), "error": "permission denied"})
            continue
        except OSError as error:
            report["errors"].append({"path": display_path(directory), "error": error.strerror or str(error)})
            continue
        for item in entries:
            # Hidden children (e.g. ~/.codex/skills/.system) are not loaded through a parent root.
            if item.name in SKIP_DIRS or item.name.startswith(".") or (depth == 0 and item.name in skip_children):
                continue
            try:
                if item.is_dir(follow_symlinks=True):
                    stack.append((Path(item.path), depth + 1))
            except OSError as error:
                report["errors"].append({"path": display_path(item.path), "error": error.strerror or str(error)})
    return found


def project_directories(cwd: Path):
    """cwd and its parents up to the git root; only cwd when not in a repo."""
    chain = []
    for directory in [cwd, *cwd.parents]:
        chain.append(directory)
        if (directory / ".git").exists():
            return chain, directory
    return [cwd], None


# ------------------------------------------------------------------ settings

def mini_toml(text: str):
    """Fallback for Python < 3.11: extracts only the tables this script needs."""
    data = {"skills": {"config": [], "bundled": {}}, "plugins": {}}
    current = None
    for raw in text.splitlines():
        line = raw.split(" #")[0].strip()
        if not line or line.startswith("#"):
            continue
        if line == "[[skills.config]]":
            current = {}
            data["skills"]["config"].append(current)
        elif line == "[skills.bundled]":
            current = data["skills"]["bundled"]
        elif line.startswith("[plugins."):
            name = unquote(line[len("[plugins."):-1])
            current = data["plugins"].setdefault(name, {})
        elif line.startswith("["):
            current = None
        elif current is not None and "=" in line:
            key, value = (part.strip() for part in line.split("=", 1))
            current[key] = is_true(value) if value in ("true", "false") else unquote(value)
    return data


def load_toml(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    try:
        import tomllib  # Python 3.11+
        return tomllib.loads(text)
    except ImportError:
        return mini_toml(text)


def load_settings(config, home, project_dirs, system_root, os_name, report):
    state = {"codex_rules": [], "codex_bundled": None, "codex_plugins": {},
             "claude_overrides": {}, "unreadable": {"codex": False, "claude": False}}
    claude_layers = []
    for entry in config.get("settings", []):
        if os_name not in entry["os"]:
            continue
        for path in resolve_bases(entry, home, project_dirs, system_root):
            if not path.is_file():
                continue
            try:
                if entry["kind"] == "codex_config":
                    data = load_toml(path)
                    skills = data.get("skills", {}) or {}
                    for rule in skills.get("config", []) or []:
                        state["codex_rules"].append(rule)
                    bundled = (skills.get("bundled") or {}).get("enabled")
                    if bundled is not None:
                        state["codex_bundled"] = bool(bundled)
                    for name, plugin in (data.get("plugins") or {}).items():
                        state["codex_plugins"][name] = plugin.get("enabled", "unknown")
                else:
                    data = json.loads(path.read_text(encoding="utf-8-sig"))
                    claude_layers.append((entry.get("rank", 0), data.get("skillOverrides") or {}))
                report["settings_read"].append(display_path(path))
            except Exception as error:  # a broken settings file must not stop the scan
                state["unreadable"][entry["tool"]] = True
                report["errors"].append({"path": display_path(path), "error": "settings unreadable: %s" % error})
    for _, overrides in sorted(claude_layers, key=lambda layer: layer[0]):
        for name, value in overrides.items():
            state["claude_overrides"][name.casefold()] = value
    return state


def codex_status(skill, level, state):
    if state["unreadable"]["codex"]:
        return "unknown"
    if level == "system" and state["codex_bundled"] is False:
        return "disabled"
    status = "enabled (default)"
    for rule in state["codex_rules"]:
        matches = False
        if "path" in rule:
            matches = path_key(rule["path"]) == path_key(skill["path"])
        elif "name" in rule:
            matches = str(rule["name"]).casefold() == skill["name"].casefold()
        if matches and "enabled" in rule:
            status = "enabled" if rule["enabled"] else "disabled"
    return status


def claude_status(skill, state):
    if state["unreadable"]["claude"]:
        return "unknown"
    value = state["claude_overrides"].get(skill["name"].casefold())
    return {None: "enabled (default)", "on": "enabled", "name-only": "enabled (name only)",
            "user-invocable-only": "explicit-only", "off": "disabled"}.get(value, "unknown")


# ------------------------------------------------------------------- plugins

def query_plugins(config, run_commands, state):
    result = {}
    for tool, spec in config.get("plugin_commands", {}).items():
        entry = {"doc": spec.get("doc")}
        command = spec.get("command")
        if tool == "codex" and state["codex_plugins"]:
            entry["from_settings"] = state["codex_plugins"]
        if not command:
            entry.update(status="uncovered", reason=spec.get("reason"))
        elif not run_commands:
            entry.update(status="uncovered", reason="plugin commands disabled (--no-plugin-commands)")
        else:
            executable = shutil.which(command[0])
            if not executable:
                entry.update(status="uncovered", reason="%s CLI not found on PATH" % command[0])
            else:
                try:
                    completed = subprocess.run(
                        [executable, *command[1:]], capture_output=True, timeout=20,
                        env={**os.environ, **spec.get("env", {})}, stdin=subprocess.DEVNULL)
                    output = completed.stdout.decode("utf-8", "replace").strip()
                    if completed.returncode == 0:
                        entry.update(status="listed (names only; skill paths not provided)",
                                     command=" ".join(command), output=output[:6000])
                    else:
                        entry.update(status="uncovered", command=" ".join(command),
                                     reason="exit code %d: %s" % (completed.returncode,
                                     completed.stderr.decode("utf-8", "replace").strip()[:500]))
                except (OSError, subprocess.TimeoutExpired) as error:
                    entry.update(status="uncovered", reason="command failed: %s" % error)
        result[tool] = entry
    return result


# ---------------------------------------------------------------------- main

def detect_host(config, requested):
    if requested:
        return requested, "flag"
    for tool, spec in config["tools"].items():
        if any(os.environ.get(variable) for variable in spec.get("host_env", [])):
            return tool, "environment"
    return "unknown", "not detected"


def resolve_conflicts(skills, config):
    groups = {}
    for skill in skills:
        groups.setdefault(skill["name"].casefold(), []).append(skill)
    conflicts = []
    for name, group in groups.items():
        if len(group) < 2:
            continue
        per_tool = {}
        for tool, spec in config["tools"].items():
            seen = [(skill, skill["tools"][tool]["level"]) for skill in group if tool in skill["tools"]]
            if len(seen) < 2:
                continue
            order = spec.get("name_precedence") or []
            ranked = sorted(seen, key=lambda pair: order.index(pair[1]) if pair[1] in order else len(order))
            first_level = ranked[0][1]
            winners = [skill for skill, level in ranked if level == first_level]
            if order and first_level in order and len(winners) == 1:
                per_tool[tool] = {"effective": winners[0]["path"], "rule": spec["name_conflict_rule"]}
            else:
                per_tool[tool] = {"effective": None, "ambiguous": True, "rule": spec["name_conflict_rule"]}
        conflicts.append({"name": group[0]["name"], "paths": [skill["path"] for skill in group],
                          "identical_content": len({file_digest(skill["path"]) for skill in group}) == 1,
                          "per_tool": per_tool})
    return conflicts


def file_digest(path: str) -> str:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return "unreadable:" + path


def brief_label(skill, repeated):
    """Same-name skills in one group keep both descriptions, disambiguated by path."""
    if skill["name"] in repeated:
        return "%s @ %s" % (skill["name"], skill["path"])
    return skill["name"]


def brief_groups(skills):
    """Group skills by '<host> | tool:level[:flags], ...' so shared labels are written once."""
    grouped, problems = {}, {}
    for skill in skills:
        if skill.get("is_self"):
            continue
        seen_in = []
        for tool, info in sorted(skill["tools"].items()):
            label = "%s:%s" % (tool, info["level"])
            if info["enabled"] == "disabled":
                label += ":disabled"
            if info["invocation"] == "explicit-only":
                label += ":explicit-only"
            seen_in.append(label)
        key = "%s | %s" % (skill["host"], ", ".join(seen_in))
        grouped.setdefault(key, []).append(skill)
        if skill.get("problems"):
            problem_key = skill["name"]
            if problem_key in problems:
                problem_key = "%s @ %s" % (skill["name"], skill["path"])
            problems[problem_key] = skill["problems"]
    groups = {}
    for key, items in grouped.items():
        repeated = {item["name"] for item in items if sum(1 for other in items if other["name"] == item["name"]) > 1}
        groups[key] = {brief_label(item, repeated): item["description"] for item in items}
    return dict(sorted(groups.items())), problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", choices=["claude", "codex", "cursor"], help="tool this agent runs in")
    parser.add_argument("--cwd", type=Path, help="project directory (default: current directory)")
    parser.add_argument("--home", type=Path, help="home directory override (tests with fake folders)")
    parser.add_argument("--os", dest="os_name", choices=["windows", "macos", "linux"], help="OS override (tests)")
    parser.add_argument("--system-root", type=Path, help="re-root absolute locations under this folder (tests)")
    parser.add_argument("--locations", type=Path, default=DEFAULT_LOCATIONS)
    parser.add_argument("--max-desc", type=int, default=0, help="truncate descriptions to N chars (0 = full)")
    parser.add_argument("--brief", action="store_true", help="compact first-pass inventory")
    parser.add_argument("--only", help="comma-separated skill names to report in full")
    parser.add_argument("--no-plugin-commands", action="store_true")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    config = json.loads(args.locations.read_text(encoding="utf-8-sig"))
    os_name = args.os_name or current_os()
    home = (args.home or Path.home()).absolute()
    cwd = (args.cwd or Path.cwd()).absolute()
    project_dirs, repo_root = project_directories(cwd)
    host, host_source = detect_host(config, args.host)

    report = {"locations_scanned": [], "locations_missing": [], "errors": [], "broken": [],
              "settings_read": []}
    state = load_settings(config, home, project_dirs, args.system_root, os_name, report)

    by_identity = {}
    for order, entry in enumerate(config["locations"]):
        if os_name not in entry["os"]:
            continue
        for root in resolve_bases(entry, home, project_dirs, args.system_root):
            if not root.is_dir():
                if entry["base"] != "project":
                    report["locations_missing"].append(
                        {"tool": entry["tool"], "level": entry["level"], "path": display_path(root)})
                continue
            report["locations_scanned"].append(
                {"tool": entry["tool"], "level": entry["level"], "path": display_path(root)})
            for skill_dir in find_skill_dirs(root, entry.get("max_depth", 1),
                                             set(entry.get("skip_children", [])), report):
                skill_file = skill_dir / SKILL_FILE
                identity = path_key(skill_file)
                sighting = {"tool": entry["tool"], "level": entry["level"], "path": display_path(skill_file)}
                if identity in by_identity:
                    by_identity[identity]["seen_from"].append(sighting)
                    by_identity[identity]["_orders"].append((order, len(str(root))))
                    continue
                fields, error = read_frontmatter(skill_file)
                if error:
                    seen_from = [sighting]
                    report["broken"].append({"path": display_path(skill_file), "error": error,
                                             "seen_from": seen_from})
                    by_identity[identity] = {"broken": True, "seen_from": seen_from, "_orders": []}
                    continue
                by_identity[identity] = {"fields": fields, "dir": skill_dir, "file": skill_file,
                                         "seen_from": [sighting], "_orders": [(order, len(str(root)))]}

    skills = []
    self_key = path_key(SELF_DIR / SKILL_FILE)
    for identity, item in by_identity.items():
        if item.get("broken"):
            continue
        fields, skill_dir = item["fields"], item["dir"]
        problems = []
        name = fields.get("name") or ""
        if not name:
            problems.append("missing name (folder name used)")
            name = skill_dir.name
        elif name != skill_dir.name:
            problems.append("name differs from folder name %r" % skill_dir.name)
        if not NAME_PATTERN.match(name):
            problems.append("name is not lowercase-hyphen")
        description = fields.get("description") or ""
        if not description:
            problems.append("missing description")
        elif len(description) > 1024:
            problems.append("description longer than 1024 chars")
        if args.max_desc and len(description) > args.max_desc:
            description = description[:args.max_desc].rstrip() + "…"

        explicit_only = is_true(fields.get("disable-model-invocation", "false"))
        codex_implicit, dependency_hints = codex_implicit_policy(skill_dir)
        real_file = display_path(os.path.realpath(str(item["file"])))
        skill = {"name": name, "description": description, "path": real_file,
                 "seen_from": item["seen_from"], "tools": {}}

        # Most specific location wins the level label when one tool sees a skill twice.
        for sighting, (order, root_len) in sorted(zip(item["seen_from"], item["_orders"]),
                                                   key=lambda pair: (-pair[1][1], pair[1][0])):
            tool = sighting["tool"]
            if tool in skill["tools"]:
                continue
            level = sighting["level"]
            info = {"level": level}
            if tool == "codex":
                info["enabled"] = codex_status(skill, level, state)
                info["invocation"] = "explicit-only" if codex_implicit is False else "auto"
            elif tool == "claude":
                info["enabled"] = claude_status(skill, state)
                info["invocation"] = "explicit-only" if explicit_only or info["enabled"] == "explicit-only" else "auto"
            else:
                info["enabled"] = "unknown"
                info["invocation"] = "explicit-only" if explicit_only else "auto"
            skill["tools"][tool] = info

        if host == "unknown":
            skill["host"] = "unknown-host"
        elif host in skill["tools"]:
            skill["host"] = "disabled-in-host" if skill["tools"][host]["enabled"] == "disabled" else "invocable"
        else:
            skill["host"] = "other-tool-only"
        skill["runnable"] = "unverified"
        if dependency_hints:
            skill["dependency_hints"] = dependency_hints
        if problems:
            skill["problems"] = problems
        if identity == self_key:
            skill["is_self"] = True
        skills.append(skill)

    skills.sort(key=lambda skill: (skill["name"].casefold(), skill["path"]))
    synced_found = any(s["tools"].get("claude", {}).get("level") == "synced" for s in skills)
    output = {
        "host": {"tool": host, "detected_by": host_source, "os": os_name},
        "cwd": display_path(cwd),
        "repo_root": display_path(repo_root) if repo_root else None,
        "counts": {"skills": len(skills), "broken": len(report["broken"]),
                   "duplicates_merged": sum(len(s["seen_from"]) - 1 for s in skills),
                   "by_tool": {tool: sum(1 for s in skills if tool in s["tools"]) for tool in config["tools"]}},
        "skills": skills,
        "name_conflicts": resolve_conflicts(skills, config),
        "plugins": query_plugins(config, not args.no_plugin_commands, state),
        "claude_ai_synced": "found under ~/.claude/skills/synced" if synced_found else
            "none found locally; claude.ai account skills are not local unless synced",
        **report,
    }
    if args.only:
        wanted = {name.strip().casefold() for name in args.only.split(",") if name.strip()}
        output["skills"] = [s for s in skills if s["name"].casefold() in wanted]
        output["name_conflicts"] = [c for c in output["name_conflicts"] if c["name"].casefold() in wanted]
    elif args.brief:
        output["skills"], output["problems"] = brief_groups(skills)
        output["name_conflicts"] = [
            {"name": c["name"], "identical_content": c["identical_content"],
             "ambiguous_in": [tool for tool, info in c["per_tool"].items() if info.get("ambiguous")]}
            for c in output["name_conflicts"]]
        output.pop("locations_scanned")
    json.dump(output, sys.stdout, ensure_ascii=False, indent=None if args.brief else 1)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
