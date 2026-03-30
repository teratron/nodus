# Project Specification Rules
**Version:** 1.1.0
**Status:** Active

## Overview
Constitution of the specification system for this project.
Read by the agent before every operation. Updated only via explicit triggers.

## 1. Naming Conventions
- Spec files must include a layer prefix (e.g., `l1-`, `l2-`), followed by lowercase kebab-case: `l1-api.md`, `l2-database-schema.md`.
- System files use uppercase: `INDEX.md`, `RULES.md`.
- Section names within specs are title-cased.

## 2. Status Rules
- **Draft → RFC**: all required sections filled, ready for review.
- **RFC → Stable**: reviewed, approved, no open questions.
- **RFC → Draft**: needs rework or significant revision.
- **Stable → RFC**: substantive amendment (minor/major bump) requires re-review.
- **Any → Deprecated**: explicitly superseded; replacement must be named.

## 3. Versioning Rules
- `patch` (0.0.X): typo fixes, clarifications — no structural change.
- `minor` (0.X.0): new section added or existing section extended.
- `major` (X.0.0): structural restructure or scope change.

## 4. Formatting Rules
- Use `plaintext` blocks for all directory trees.
- Use `mermaid` blocks for all flow and architecture diagrams.
- Do not use other diagram formats.

## 5. Content Rules
- No implementation code (no Rust, JS, Python, SQL, etc.).
- Pseudo-code and logic flows are permitted.
- Every spec must have: Overview, Motivation, Document History.

## 6. Relations Rules
- Every spec that depends on another must declare it in `Related Specifications`.
- Cross-file content duplication is not permitted — use a link instead.
- Circular dependencies must be flagged and resolved.

## 7. Project Conventions

### C1 — `.magic/` Engine Safety

`.magic/` is the active SDD engine. Any modification must follow this protocol:

1. **Read first** — open and fully read every file that will be affected.
2. **Analyse impact** — trace how the changed file is referenced by other engine files and workflow wrappers.
3. **Verify continuity** — confirm that after the change all workflows remain fully functional.
4. **Never edit blindly** — if the scope of impact is unclear, stop and ask before proceeding.
5. **Document the change** — record modifications in the relevant spec and commit message.
6. **Atomic Update** — apply changes simultaneously across all related files (scripts, workflows, and documentation) to maintain full engine consistency.
7. **No-Change, No-Bump** — NEVER trigger a version bump (C14) if no physical files in `.magic/` were modified (e.g., during dry runs or purely cognitive tasks).

### C2 — Workflow Minimalism

Limit the SDD workflow to the core command set to maximize automation and minimize cognitive overhead. Do not introduce new workflow commands unless strictly necessary and explicitly authorized as a C2 exception.

### C3 — Parallel Task Execution Mode

Task execution defaults to **Parallel mode**. A Manager Agent coordinates execution, reads status, unblocks tracks, and escalates conflicts. Tasks with no shared constraints are implemented in parallel tracks.

### C4 — Automate User Story Priorities

Skip the user story priority prompt. The agent must automatically assign default priorities (P2) to User Stories during task generation to maximize automation and avoid interrupting the user.


### C6 — Selective Planning

During plan updates, specs are handled by their status:
- **Draft specs**: automatically moved to `## Backlog` in `PLAN.md` without user input.
- **RFC specs**: surfaced to user with a recommendation to backlog until Stable.
- **Stable specs**: agent asks which ones to pull into the active plan. All others go to Backlog.
- **Orphaned specs** (in INDEX.md but absent from both plan and backlog): flagged as critical blockers.

### C7 — Universal Script Executor

All automation scripts must be invoked via the cross-platform executor:
`node .magic/scripts/executor.js <script-name> [args]`

Direct calls to `.sh` or `.ps1` scripts are not permitted in workflow instructions. The executor detects the OS and delegates to the appropriate implementation.

### C8 — Phase Archival

On phase completion, the per-phase task file is moved from `$DESIGN_DIR/tasks/` to `$DESIGN_DIR/archives/tasks/`. The link in `TASKS.md` is updated to point to the archive location. This keeps the active workspace small while preserving full history.

### C9 — Zero-Prompt Automation

Once the user approves the plan and task breakdown, the agent proceeds through execution and conclusion workflows without further confirmation prompts. Silent operations include: retrospective Level 1, changelog Level 1, CONTEXT.md regeneration, and status updates. The single exception is changelog Level 2 (external release artifact) which requires one explicit user approval before writing.
**Phase Gates Exception**: C9 applies ONLY within a specific executing phase (e.g., executing atomic tasks within magic.run). Transitions across major workflow boundaries (Spec → Task → Run) constitute 'Phase Gates' and ALWAYS require explicit user approval (Hard Stop) before handing off.

### C10 — Nested Phase Architecture

Implementation plans in `PLAN.md` must follow a nested hierarchy: **Phase → Specification → Atomic Tasks**. Each specification is decomposed into 2–3 atomic checklist items using standardized notation:
- `[ ]` Todo
- `[/]` In Progress
- `[x]` Done
- `[~]` Cancelled
- `[!]` Blocked

### C11 — [RESERVED]

This rule ID is reserved for future extensions.

### C12 — Quarantine Cascade (Каскад Карантина)

If a Layer 1 (Concept) specification loses its `Stable` status or is removed, all dependent Layer 2/3 (Implementation) specifications must automatically and transparently be treated as demoted to `RFC` or moved to the Backlog by the Task workflow. The system must quarantine dependent specifications to prevent "orphaned" task scheduling without requiring manual status edits for every child in `INDEX.md`.

**C12.1 — Stabilization Exception**: Tasks explicitly intended to stabilize or fix mismatches to regain `Stable` status for the parent may bypass this quarantine.

### C13 — Agent Cognitive Discipline

All AI agents operating within the Magic SDD framework must adhere to strict cognitive discipline to prevent hallucinations and silent failures:

1. **Primary Source Principle**: Always read original `.magic/` and `.design/` files. Never rely on cached memory or interpretive assumptions.
2. **Anti-Truncation**: Execute checklists and multi-step processes literally. Do not skip, merge, or summarize steps.
3. **Zero Assumptions**: If an instruction is absent or ambiguous, halt and ask for clarification. Do not invent missing steps or scripts.
4. **Mandatory Self-Verification**: Cross-reference actions against original instructions before finalizing any task or presenting a completion checklist.
5. **Anti-Hallucination Audit**: All architectural conclusions, problem reports, and proposed changes must be directly traceable to specific statements within project specifications or engine rules.

### C14 — Engine Versioning Protocol

To ensure accurate engine state tracking and reliable updates, any modification to the core engine/kernel files (anything inside the `.magic/` directory, including workflows and templates) MUST be accompanied by an automated engine metadata update: `node .magic/scripts/executor.js update-engine-meta --workflow {workflow}`.

1. **Scope**: Applies to all `.md` workflows, `scripts/`, `templates/`, and `config.json` inside the engine directory.
2. **Automation**: This command automatically increments the patch version in `.magic/.version`, updates the relevant history file in `.magic/history/`, and regenerates `.magic/.checksums`. **Smart History**: Redundant automated entries are skipped if the last entry matches.
3. **Exclusion**: Modifications to `.design/` files (project content) do NOT trigger an engine version bump; they trigger project manifest bumps instead.
4. **Synchronization**: The version in `.magic/.version` should stay aligned with the latest meaningful change to the engine's functional logic.
5. **Cognitive Exemption**: Purely cognitive tasks, dry runs, or audit tasks that do not modify files MUST NOT trigger a C14 version bump to avoid metadata noise.

### C15 — Workspace Scope Isolation

When operating in a workspace with a defined scope (via `.design/workspace.json`), the agent MUST restrict all analysis and file operations to the directories specified in the scope. All other project directories are treated as out-of-scope to ensure logical isolation and prevent context leakage or accidental modification of unrelated modules.

### C16 — Micro-spec Convention

For minor features, simple bugfixes, or changes expected to be under 50 lines of documentation, the agent is authorized to use the lightweight `.magic/templates/micro-spec.md` instead of the full specification template. If a Micro-spec exceeds 50 lines or architectural complexity increases, it MUST be promoted to the full Standard template.

### C17 — Session Isolation (Phase Gates)

To prevent context bleed-over and hallucination loops, the SDD workflow strictly separates Brainstorming, Planning, and Execution phases into isolated context windows.
1. **Brainstorming & Spec Generation (Phase 1)**: Must be completed within a single, continuous chat session so the agent retains the context of the evolving idea. Do not break the session until specs are marked `Stable`.
2. **Phase Transition (Phase Gates)**: Once a major phase completes (e.g., Specs are `Stable`), the current chat MUST be closed. **Note**: giving a text command like "forget previous instructions" does NOT clear context memory reliably. You must physically click the "New Chat" (or equivalent) button in your IDE/interface.
3. **Execution (Phases 2 & 3)**: Planning (`/magic.task`) and Coding (`/magic.run`) MUST each be started in a brand-new, clean chat session. This forces the agent to read the committed files as the singular source of truth, eliminating reliance on ephemeral chat memory.

### C18 — Payload Security

The installers (Node/Python) must verify payload integrity (checksums) and prevent Path Traversal attacks during extraction. Deployment must be atomic to prevent partial engine states.

### C19 — Cross-Env CLI Parity

Node and Python installers must maintain strict CLI parity. Every command-line flag (e.g., `--yes`, `--update`, `--check`) must behave identically across both implementations to ensure a consistent user experience.

### C20 — Auto-Heal Recovery

The engine must proactively identify and repair its own metadata. If `executor.js` detects missing history files or corrupted checksums during non-critical operations, it should attempt to "Auto-Heal" (restore defaults or regenerate) before Proceeding or Halting.

### C21 — Project Ventilation (Analyze)

The command `/magic.analyze` (or `Analyze project`) triggers "Project Ventilation": a deep scan that treats the current codebase as the source of truth and compares it against `INDEX.md` and `RULES.md`. It must identify:

- **Registry Drift**: Specs in INDEX but missing on disk.
- **Coverage Gaps**: Code folders without corresponding specs.
- **Rule Violations**: Code patterns that contradict `RULES.md §7` (both global and workspace tiers).
- **Integrity Issues**: Mismatched checksums in `.magic/`.

### C22 — Workspace Rule Inheritance

Each workspace may maintain a local `RULES.md` at `.design/{workspace}/RULES.md`. These files:

1. Contain only workspace-specific §7 conventions, identified as `WC1`, `WC2`, … (workspace convention).
2. Inherit all §1–6 universal rules and global §7 conventions from `.design/RULES.md` — no re-declaration needed.
3. Must not contradict the global constitution (Constitutional Guard applies equally).
4. Are created on demand by `magic.rule` when the first workspace-scoped rule is requested.
5. Version independently from the global `RULES.md`.

### C23 — Context Economy & Validation Caching

To minimize redundant resource usage and improve performance, the agent may optimize `check-prerequisites` calls within a single task lifecycle:

1. **Turn-Aware Caching**: If `check-prerequisites` returned `ok: true` earlier in the current conversation turn or the immediately preceding turn, and the agent has NOT modified any files in `.magic/` or `.design/` since that check, the agent is authorized to skip the physical script execution and rely on the known "Clean State".
2. **External Drift Guard**: If a significant time has passed or the user has performed manual file operations (e.g. `git pull`, manual edits in terminal), the agent MUST perform a fresh `check-prerequisites` call.
3. **Halt Persistence**: If the previous check returned an error or warning (e.g. `checksums_mismatch`), the agent MUST re-run the check after any attempt to fix it. Never assume a "heal" without verification.
4. **Audit Exemption**: In `/magic.analyze` (Ventilation), caching is NOT permitted. These workflows must perform fresh, physical scans by definition to fulfill their audit purpose.

### C24 — Python Toolchain Protocol

The project strictly adheres to `uv`-first philosophy.
- **Environment**: Always initialize and activate with `.venv` and `uv sync`.
- **Formatting & Linting**: `uv run ruff check --fix` and `uv run ruff format`.
- **Static Analysis**: `uv run pyrefly check`
- **Target**: Python 3.12+ features must be supported.

### C25 — Python Design Aesthetics

- **Sectioning**: Use uniform Unicode-based block separators (e.g. `═════════════════════`) for major bounds and `─────────────────────` for minor groups instead of excessive whitespace.
- **Docstrings**: Adhere strictly to Google-style docstrings with `Args:`, `Returns:`, and `Raises:` clauses.
- **Imports**: Include `from __future__ import annotations` at the top of every python file.

### C26 — Testing Guardrails

- **Runner**: All tests use `pytest`. Command: `uv run pytest`.
- **Structure**: Tests must be structurally aligned and separated into an independent test folder outside of target module sources.

### C27 — Junction Safety (Windows)

When managing `git` with mapped junction paths (e.g. `mklink /J`):
- `git rm -r --cached <path>` is prohibited against mapped junction boundaries, as it physically deletes files in the target.
- Rule: Always `git rm --cached` files explicitly *before* establishing junctions, or reference file paths sequentially tracking over boundaries.

### C28 — Bilingual Communication Protocol

- **Code & Docs**: All identifiers, code artifacts, comments, docstrings, commits, PRs, and system messages MUST be in English.
- **Interactions**: Strategy, reasoning, plan elaboration, and chat messaging MUST be conducted in Russian to ensure alignment with team protocols.

## Document History
| Version | Date | Description |
| :--- | :--- | :--- |
| 1.0.0 | 2026-03-30 | Initial constitution |
| 1.1.0 | 2026-03-30 | Scaffolded missing project rules C24-C28 |
