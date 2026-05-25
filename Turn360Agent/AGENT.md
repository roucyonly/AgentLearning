# AGENT.md

This file is for development agents working in this repository. It defines engineering workflow rules, not product judgment or dialogue persona rules. Product design principles live in `project.md` and `docs/`.

## 1. Before Working

- Read `project.md`, `docs/README.md`, and the module docs related to the task before editing.
- Check `git status --short` before making changes.
- Treat existing uncommitted changes as user work unless you made them in the current task.
- Do not revert, overwrite, or reformat unrelated files.
- Keep changes scoped to the user's request.

## 2. Editing Rules

- Prefer small, reviewable changes over broad rewrites.
- Follow existing file structure and terminology.
- Use structured data formats for cases and configs; avoid free-form blobs when fields will be read by code.
- When changing formulas, API contracts, UI routes, data models, or case schemas, update the related docs in the same task.
- When adding or changing user-facing flows, update QA expectations.
- Use clear field names and include units in schema fields when values are numeric.

## 3. Testing And Verification

- Run the narrowest useful verification after each meaningful change.
- For JSON files, parse them after editing.
- For docs that reference files or symbols, run `rg` checks to verify links and terminology.
- For frontend work, verify the local UI in a browser and capture screenshots when practical.
- If a test cannot be run, say why in the final response.

## 4. Git Discipline

- Work in small logical units that can become atomic commits.
- Before proposing a commit, inspect `git diff --stat` and `git diff`.
- Stage only files related to the current task.
- Commit promptly after a coherent task is complete when the user asks for commits or the session workflow expects commits.
- Use clear commit messages that describe the actual change, for example:
  - `docs: add mvp seed case finance indicators`
  - `feat: add pre-opening finance calculation mode`
  - `test: cover breakeven target order calculation`
- Do not hide unrelated modified files inside a commit.

## 5. Documentation Discipline

- Keep `project.md` for product scope and high-level decisions.
- Keep `docs/` for technical design, formulas, UI maps, API contracts, QA plans, and seed cases.
- Keep this `AGENT.md` for development workflow rules only.
- If a rule belongs to product behavior, put it in the relevant product or technical doc, not here.

## 6. Communication

- Give concise progress updates during multi-step work.
- Call out assumptions when data is incomplete.
- In the final response, summarize changed files, verification performed, and any remaining gaps.

