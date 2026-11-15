# Skills

My personal collection of skills for AI assistants. Each skill lives in its own folder, with its main instructions in a `SKILL.md` file.

## Available skills

| Skill | Purpose |
| --- | --- |
| [agile-team](skills/agile-team/SKILL.md) | Implement features and fixes in stages, with acceptance criteria, security review, and product verification. |

## Repository structure

```text
Skills/
├── README.md
├── .gitignore
└── skills/
    └── agile-team/
        └── SKILL.md
```

When needed, a skill can include `scripts/` for executable helpers, `references/` for supporting documentation, and `assets/` for files used in its output.

## Adding a skill

1. Create a folder inside `skills/` using lowercase letters and hyphens, such as `laravel-helper`.
2. Add a `SKILL.md` file. Adapt this example to your skill's actual purpose:

```markdown
---
name: laravel-helper
description: Review Laravel controllers for validation and authorization issues.
---

# Laravel Helper

Use this skill when reviewing Laravel controllers.

1. Check request validation.
2. Check authorization for the requested action.
3. Report actionable findings with file locations and suggested fixes.
```

3. Explain when to use the skill, which steps to follow, and what output to produce. Keep the folder name and the `name` field consistent.
4. Add a link and a short description to the skills table above.
5. Review and publish your changes:

```powershell
Set-Location 'D:\My-skills'
git status
git diff
git add -- skills/laravel-helper README.md
git diff --cached
git commit -m "Add laravel-helper skill"
git push
```

## Getting started

Clone the repository:

```powershell
git clone https://github.com/Artashok11228/Skills.git
```

Copy the skill folder you want to use into your AI tool's skills directory. Installation paths and activation steps depend on the tool. Cloning this repository alone does not activate the skills.

## Maintenance

- Give each skill its own folder and a clear purpose.
- Add supporting files only when they are needed.
- Keep passwords, tokens, environment files, and private information out of the repository.
- Review staged changes with `git diff --cached` before publishing.
- Before distributing the skills for others to use, choose an appropriate license and add a `LICENSE` file.
