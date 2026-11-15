---
name: agile-team
description: Implement multi-step features and fixes with task acceptance criteria, product verification, and security review. Use for phased implementation or requests for an agile, scrum, or reviewed task workflow. Use the lightweight path for small changes when explicitly invoked; routine questions and standalone status reports do not need this workflow.
---

# agile-team

Use three perspectives: Product Owner (PO), Developer (Dev), and Security Reviewer (Sec). A single agent can apply them sequentially without special tools. Switching perspectives is self-review, not an independent review. Keep role transitions internal unless explaining one helps the user make a decision.

## Start with the project

Before defining tasks, read the applicable project instructions, inspect existing changes and the relevant code, and identify available checks. Preserve the user's existing work. Keep this inspection focused on the requested change.

Identify the user's problem, intended behavior, and smallest useful result. Separate explicit requirements from assumptions and optional suggestions; optional improvements do not become acceptance criteria without authorization.

For a low-risk ambiguity, state a reasonable assumption briefly and proceed. Ask a focused question when the answer materially changes scope, core product behavior, data integrity, or an irreversible action. Continue independent work while waiting; leave dependent work pending. Reuse decisions and authorization already given in the conversation.

## Choose a proportional path

- **Lightweight:** A small, localized, low-risk change. State the intended result briefly, implement it, inspect the actual change, run suitable checks, and report the result. Apply relevant product and security checks without separate role reports or a formal task breakdown.
- **Full:** A multi-part change, cross-component behavior, or sensitive work such as authorization, payments, data migrations, or destructive operations. Use the task workflow below.

Both paths require evidence before completion and follow the same rules for findings and unresolved work. If inspection reveals greater risk or dependencies, switch to the full path.

## Full task workflow

PO defines a short task list grounded in the project. Each task has a goal, observable acceptance criteria, dependencies, and a brief scope boundary where useful. Share the plan and proceed within the authorized scope; request a decision only for a material unresolved choice.

For example, replace "login is secure" with "an incorrect password is rejected and the response does not disclose whether the account exists."

Work on one task at a time:

1. **PO defines the result.** Confirm the task's criteria and dependencies.
2. **Dev implements.** Make the smallest coherent change, follow existing conventions, and avoid unrelated refactoring. Choose validation based on the affected behavior and risk.
3. **Sec reviews.** Inspect the actual diff and relevant callers or configuration. Check applicable risks: validation, authentication, authorization, injection, exposed secrets, file or network access, sensitive logging, and dependency changes. Keep the review scoped to the change and its consequences.
4. **PO verifies.** Compare the implementation with the user's request and every acceptance criterion. Record each as passed, failed, or unverified, with supporting evidence or the reason it remains open.
5. **Review and resolve.** Apply the review loop and completion rules below.

## Evidence and validation

Check the changed behavior's success path, failure path, and relevant edge cases. Select tests because they can catch a meaningful failure, not merely because the project already has a test suite.

- For a bug fix, add or adapt a regression test where feasible and confirm it exercises the reported failure.
- For important behavior or security changes, use focused automated checks where feasible, including when the project lacks an established suite.
- For low-impact text or visual edits, a focused inspection or rendered check may be sufficient.
- If a check cannot run, report the reason, what was checked instead, and the behavior that remains unverified. Inspection alone does not establish runtime behavior.

Support findings with the location, failure scenario, impact, severity, suggested fix, and relevant evidence. Distinguish a demonstrated defect from a plausible concern that still needs investigation. Reference file locations or check results when they help substantiate a conclusion; never expose secrets in reports.

When a review finds nothing, say "No findings in the reviewed scope" and identify the scope and checks. This is not a guarantee that the software is defect-free.

## Review loop and completion

One review round means examining the current result against the request, criteria, actual diff, and validation evidence. Look for missing requirements, functional defects, relevant security risks, unrelated changes, unnecessary complexity, and gaps in verification.

If findings remain, fix the affected part, then repeat the affected checks and inspect the fix for regressions. Re-plan the task only if its assumptions or scope changed. Allow up to three review rounds per task or phase; the limit bounds repeated review, not ordinary implementation steps.

Classify each finding by severity (critical / high / medium / low) and separately decide whether it blocks completion:

- A failed acceptance criterion, a material correctness or security defect, or missing evidence for essential behavior blocks completion, regardless of its label.
- A minor issue outside the agreed acceptance criteria may be recorded for follow-up if it does not compromise the requested result. State why it does not block; keep optional improvements outside the implementation scope.
- Complete a task only when all acceptance criteria pass and no blocking findings remain. Report any nonblocking follow-ups.

After three rounds with unresolved blockers, stop repeating the same loop. Report the remaining issue, evidence, attempted fixes, and concrete next step. Do not call the task complete. Continue only tasks that are independent of the unresolved issue and can be performed safely within scope. Ask for user input only when a decision or missing information is actually needed.

Use these statuses:

- **Done:** Criteria passed and no blocking findings remain.
- **Incomplete:** Implementation or necessary verification remains.
- **Blocked:** Progress requires an unavailable dependency, capability, or external change.
- **Needs user decision:** A specific unresolved choice requires the user.

## Phase verification

A phase is a meaningful group of related tasks, not an extra ceremony after every small edit. At its end, verify the combined user flow, interfaces between components, and regressions in affected existing behavior. Passing individual task checks does not prove integration works.

Use the same bounded review loop for integration findings. Reuse valid task-level evidence; repeat checks when integration changes or new evidence warrant it. A phase is complete only when its constituent tasks are complete and its integration criteria pass.

## Reporting

Keep updates proportional to the work. Report meaningful results, blockers, and decisions rather than narrating each role switch.

For a full task, briefly show the result against acceptance criteria, important changes, checks actually performed, material findings or follow-ups, and status. Mention review round counts only when they explain unresolved work. At phase end, summarize the working user flow, verification limits, and any decisions needed.

For a lightweight task, a short result and validation note are enough. State remaining uncertainty plainly; never describe planned checks as executed checks.
