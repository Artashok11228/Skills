---
name: the-commander
description: >-
  «با اسکیل‌هایی که دارم از کجا شروع کنم؟»، «کدام اسکیل برای این کار مناسب است؟»،
  «اگر اسکیل مناسب ندارم چه چیزی بی‌پوشش می‌ماند؟»، "which of my installed skills
  fit this, and in what order?" The Commander / the-commander: plans the shortest
  workflow from local Claude Code, Codex and Cursor skills: role, order, input and
  output, required or optional, gaps. برنامه‌ریز مسیر با اسکیل‌های نصب‌شده؛ فقط
  برنامه می‌دهد و چیزی اجرا نمی‌کند. Not for a simple task that needs no skill
  choice, such as a direct code edit.
---

# The Commander

Turns "here is my goal / situation" into a short, ordered plan built only from skills that exist on this machine.

## Boundaries

- Deliver a plan only. Do not invoke, install, edit or copy any skill; do not change the project, send messages, publish or deploy. A plan is not permission for any of these.
- If the user later asks to carry out the plan, treat each step as its own request.
- Never say a skill ran. If the host cannot invoke a chosen skill, state the real way to use it.
- Running the read-only inventory script, reading `SKILL.md` files, and read-only project checks (reading files, `git status`, `where`/`command -v`) are part of planning, even when the user says «چیزی اجرا نکن». Skip them only if the user forbids running any command; then use your context's skill list and say which tools went unchecked.
- Never recommend this skill itself (`"is_self": true` in full output).
- If the request is simple and needs no skill choice, skip this workflow and just answer.

## Workflow

**1. Frame the request.** Extract only what changes the choice: goal, current state, constraints (time, cost, access, tools), sensitivity (real users, money, personal data, production), and what is out of scope. If one missing fact would change which skills or which order, ask exactly one specific question. Otherwise state a reasonable assumption and continue.

**2. Take inventory.** Run the script (`<skill-dir>` is the folder containing this file; `--host` is the tool you run in: `claude`, `codex` or `cursor`; `--cwd` is the project the user is working on, if that differs from the current directory):

- Windows: `py -3 "<skill-dir>/scripts/discover.py" --host <host> --brief --max-desc 120`
  (no `py`? use `python`; avoid `python3`, often a Microsoft Store stub on Windows)
- macOS / Linux: `python3 "<skill-dir>/scripts/discover.py" --host <host> --brief --max-desc 120`

`<host>` is the tool you are running in: `claude`, `codex` or `cursor`. Pass `--cwd` when the user's project is not the current directory.

The script only reads. In brief mode `skills` groups `{name: description}` under keys like `invocable | codex:personal, cursor:personal:explicit-only`, meaning host label `|` each `tool:level[:disabled][:explicit-only]`. Also check `name_conflicts`, `plugins`, `broken`, `locations_missing` and `errors`. For full detail on candidates (full description, paths, per-tool state), rerun with `--only name1,name2` instead of `--brief`. Field meanings and per-tool rules are in [references/discovery.md](references/discovery.md).

Your own context's skill list is authoritative for what the host can invoke, including plugin skills the script cannot see. Add any skill that is there but missing from the JSON, labeled as host/plugin skill.

**3. Shortlist, then read.** From name + description pick candidates by capability (usually 3–8). Read the full `SKILL.md` of candidates only. Note what each really does, what input it needs, what it produces, and its dependencies (MCP server, CLI such as `semgrep`, browser, credentials, OS). Verify cheap dependencies (tool list, `where`/`command -v`); otherwise mark them unverified.

**4. Select.**
- Match real capability to a concrete need, never name similarity.
- One best skill per need. Mention an alternative only when it differs in a way that matters (depth, cost, tool, prerequisites) and say when to prefer it.
- If one skill is enough, recommend only that one: no step list, at most one line naming a conditional alternative. More skills installed is not a reason for more steps.
- For «کدام اسکیل؟» questions, give one primary choice. Add another skill only for a separate need the user stated or a risk the request clearly implies, and name that need.
- If nothing fits a need, say so plainly and name the uncovered part.
- No numeric fit scores; give a short concrete reason.
- Same-name skills: use `name_conflicts` to say which one runs in the host, or that it is ambiguous (harmless if `identical_content`).

**5. Order.**
- Sort by dependency first (a step that consumes another's output comes after it), then risk (surface blocking or severe problems early), then rework cost (settle scope before code changes; review before fixing; re-check after fixing).
- Number a step only when its condition is already true. A skill that applies only after a finding (a known hard bug, a newly created diff, a test for a fix) stays inside the repair loop, not as its own number.
- Mark every numbered step **ضروری**, **اختیاری** or **شرطی** (state the condition).
- A readiness check consumes the checks it judges, so it comes after them and after the fix. Do not run it in parallel with those checks.
- Steps with no shared input/output and no edits to the same files may run in parallel, but only if the host supports parallel agents and the user allows it. Review steps in a plan report findings; they do not edit.
- When a step can find a serious problem, add one loop: fix → re-check with the same skill that found it → continue. Name a specialist only inside that loop, and only for the finding type it handles. Do not add a test-writing or diff-review skill unless the user asked for tests or a diff review.
- Deploy, publish, repo setup and similar steps appear only if they are in the request's scope; otherwise list them as out of scope.
- Never present completed checks as a guarantee of readiness.

**6. Answer** in Persian with the format below. A single-skill answer is about 6 lines (see example 1). Never dump the full inventory.

## Output format

```markdown
**برداشت و فرض‌ها:** هدف، وضعیت فعلی، فرض‌های مؤثر (۲ تا ۴ خط)

**اسکیل‌های منتخب**
- `skill-name` — نقش؛ چرا این (و در صورت نیاز: چرا نه جایگزین)؛ برچسب اجرا

**مسیر**
1. [ضروری] `skill-name` — ورودی: … | خروجی: … | پایان: … | بعدی وقتی: …
2. [شرطی: اگر …] …

جریان (فقط برای مسیر پیچیده): 1 → 2 → (3 ∥ 4) → 5 ↺ 3

**کمبودها و موانع:** نیاز بی‌پوشش، وابستگی تأییدنشده، پلاگین پوشش‌داده‌نشده

**اولین اقدام:** یک کار مشخص و قابل انجام همین حالا
```

Execution labels (pick one, add dependency status):
- «قابل فراخوانی در همین ابزار» + how: Claude Code `/name`, Codex `$name`, Cursor `/name`. If `invocation` is `explicit-only`, say it only runs when named.
- «فقط در ابزار دیگر (<tool>)»: read its `SKILL.md` and follow it manually, or the user may copy/link it into the host's folder (their decision).
- «غیرفعال در این ابزار»: enabled only after the user changes that tool's settings.
- Dependency: «وابستگی‌ها تأیید شد» / «وابستگی تأییدنشده: …» / «اجرانشدنی: … موجود نیست». A file existing does not mean it can run.

Worked examples (fictional inventories): [references/examples.md](references/examples.md).
