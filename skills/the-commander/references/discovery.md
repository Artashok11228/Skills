# discover.py output and per-tool rules

Read this only when a field or label in the JSON is unclear.

## Options

| Option | Use |
|---|---|
| `--host claude\|codex\|cursor` | Tool you run in. Otherwise detected from env (`CLAUDECODE`, `CODEX_*`, `CURSOR_AGENT`), else `unknown`. |
| `--max-desc N` | Truncate descriptions to keep the JSON small. |
| `--brief` | First pass: `skills` is `{"<host> \| tool:level[:flags], ...": {name: description}}`. Two different files with the same name in one group use the key `name @ path`. `problems` maps names to warnings. This skill itself is omitted. |
| `--only a,b` | Full records (paths, `seen_from`, per-tool state) for the named skills only. |
| `--cwd PATH` | Project directory; project levels are scanned from here up to the git root (only this folder when not in a repo). |
| `--no-plugin-commands` | Do not run `claude plugin list`. |
| `--home`, `--os`, `--system-root`, `--locations` | Test with fake folders or another OS layout. Results from these are fictional. |

## Fields

- `skills[].path`: resolved real path of `SKILL.md`. Duplicates (same real path, case-insensitive, through symlinks or junctions) are merged; `seen_from` lists every tool/level/path that exposes it.
- `skills[].tools.<tool>.level`: `organization`, `system`, `personal`, `project`, `synced`.
- `skills[].tools.<tool>.enabled`:
  - Codex: from `[[skills.config]]` in `~/.codex/config.toml` (last match wins) and `[skills.bundled]`; default `enabled (default)`.
  - Claude Code: from `skillOverrides` (user < project < local < managed settings); `off` = disabled, `user-invocable-only` = explicit-only.
  - Cursor: no documented settings file, so always `unknown`.
- `skills[].tools.<tool>.invocation`: `explicit-only` when frontmatter has `disable-model-invocation: true` (Claude Code, Cursor) or `agents/openai.yaml` sets `allow_implicit_invocation: false` (Codex). The skill still works when named.
- `skills[].host`: `invocable` (the host reads it and it is not disabled), `other-tool-only`, `disabled-in-host`, `unknown-host`.
- `skills[].runnable`: always `unverified`; the script never checks MCP servers, CLIs or credentials.
- `name_conflicts[]`: distinct files with the same name. `per_tool.<tool>.effective` is set where the tool documents precedence (Claude Code: organization > personal > project; synced loses to any other). Codex shows both, and Cursor does not document it, so both are `ambiguous`. `identical_content: true` means the copies are byte-identical, so the conflict is harmless.
- `plugins.<tool>`: plugin skills come only from the tool's own command. `claude plugin list` gives plugin names and status but no skill paths. Codex and Cursor have no non-interactive command, so they are `uncovered`. `from_settings` lists Codex plugins enabled in `config.toml`, names only. Plugin skill paths are never guessed.
- `claude_ai_synced`: claude.ai account skills are local only when synced into `~/.claude/skills/synced/`.
- `broken[]`: unreadable `SKILL.md`, invalid UTF-8, or missing or unterminated frontmatter. Problems that don't block loading (missing name, name ≠ folder) appear under `skills[].problems`.
- `locations_missing[]`, `errors[]`: skill folders that don't exist, and access errors. Neither one stops the scan. A missing project folder is not listed: every directory from the working directory up to the repo root is checked, and most have no skills directory. A missing settings file is not an error; it means that tool's default (enabled, automatic invocation).

## Which tool reads which personal folder

| Folder | Claude Code | Codex | Cursor |
|---|---|---|---|
| `~/.claude/skills/` | yes | no | yes |
| `~/.agents/skills/` | no | yes | yes |
| `~/.codex/skills/` | no | yes (legacy) | yes |
| `~/.cursor/skills/` | no | no | yes |

No single folder covers all three tools. All locations, with their sources, are in [locations.json](locations.json).
