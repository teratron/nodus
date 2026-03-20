---
description: Workflow for analyzing existing projects and generating initial specifications.
---

# Project Analysis & Ventilation Workflow

Audits project health, syncs registries, and reverse-engineers code into `.design/` spec proposals.

**Triggers**: `/magic.analyze [arg]`, "Ventilate", "Analyze project", "Scan project", "Re-analyze"
**Examples**: `/magic.analyze`, `/magic.analyze engine`, `/magic.analyze "проверь покрытие API"`, `/magic.analyze installers "фокус на тестах"`

## Core Invariants (Mandatory)

1. **Context (Zero-Prompt)**: Resolve target workspace via the priority chain below (§Workspace Resolution). Route all logic to `.design/{workspace}/`.
2. **Auto-Init**: If `.design/` or system files missing, auto-run `.magic/init.md`.
3. **Read-Only**: Proposals only. Never modify project code or `.design/` without user approval.
4. **Artifact-First**: Write proposals/reports to agent artifacts. Only dispatch to `.design/` after approval.
5. **Bootstrapping Exemption**: Approved specs from existing code can be created directly as **Stable** L1/L2.
6. **Depth Control (Safety)**: Before scanning:
    - **<50 files**: Auto-scan.
    - **50-500 files**: Ask: Full or Focused?
    - **>500 files**: Recommend Focused/Quick. HALT for user choice.
7. **Engine Integrity (C14)**: If engine files (`.magic/`) modified → `node .magic/scripts/executor.js update-engine-meta --workflow analyze` (Smart History: redundant automated entries are skipped).

## Argument Routing

Parse the `[arg]` to determine the analysis mode:

| Input | Detection | Result |
| :--- | :--- | :--- |
| *(empty)* | No argument | **Full Analysis**: Resolve workspace via §Workspace Resolution, then Mode C → A/B |
| `engine` | Matches a workspace name in `workspace.json` | **Workspace Analysis**: Mode C (with Structural Integrity) → A/B scoped to that workspace |
| `"проверь API"` | Quoted text or text that does NOT match any workspace name | **Focused Analysis**: Mode D — interpret text as focus directive |
| `engine "фокус на тестах"` | First token is workspace + remaining is quoted text | **Workspace + Focus**: Mode D scoped to workspace |

> **Disambiguation**: If the argument is a single unquoted word that matches both a workspace name and could be a focus keyword, workspace takes priority. To force focus interpretation, wrap in quotes: `/magic.analyze "engine"`.

## Workspace Resolution

| Priority | Source | Condition | Action |
| :---: | :--- | :--- | :--- |
| 1 | **Explicit arg** | `/magic.analyze {workspace}` | Use it. Print: "Active workspace: {workspace}." Overrides `MAGIC_WORKSPACE` if both set. If name not in `workspace.json` → **HALT**: "Unknown workspace '{x}'. Available: [{list}]." |
| 2 | **`MAGIC_WORKSPACE`** | Env var set | Use it. If value not in `workspace.json` → **HALT**: "Unknown workspace '{x}'. Available: [{list}]." |
| 3 | **`workspace.json`** | Single workspace | Use it silently. |
| 3 | **`workspace.json`** | Multiple + `default` set | Use default. Print: "Active workspace: {default}." |
| 3 | **`workspace.json`** | Multiple + no `default` | **Ask**: "Which workspace to analyze? [{list}]" |
| 4 | **No `workspace.json`** | — | Use root `.design/`. Log: "No workspace config found — scanning root .design/." |

> **Scope Auto-Apply**: After workspace is resolved, apply its `scope` array from `workspace.json` as the scan boundary (equivalent to `MAGIC_WORKSPACE_SCOPE`). If the workspace has no `scope` field, scan the full project.

## Operational Logic: Scan & Infer

### 1. Stack & Structure

Identify tech stack via config files (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, etc.). Build a high-level map using directory listing (depth 2 by default; extend to depth 3 only for monorepo root directories with nested `packages/` or `apps/`).
**Isolation (C15)**: If `MAGIC_WORKSPACE_SCOPE` is defined, restrict scanning strictly to the specified directory paths.

### 2. Architecture Inference

| Pattern | Indicators |
| :--- | :--- |
| **MVC** | `controllers/`, `models/`, `views/` |
| **Clean** | `domain/`, `application/`, `infrastructure/` |
| **Feature** | `features/`, `modules/` |
| **Monorepo** | `packages/`, `apps/`, workspace configs |
| **API** | `routes/`, `handlers/`, `middleware/` |
| **UI** | `components/`, `pages/`, `hooks/` |

### 3. Module & Convention detection

Group code by domain. Extract implicit rules from configs (`.eslintrc`, `tsconfig.json`, `ruff`, etc.) for `RULES.md §7`.

## Modes: Analysis vs. Re-Analysis

### [Mode A] First-Time Analysis

*Trigger: INDEX.md is empty.*

0. **Pre-flight**: `node .magic/scripts/executor.js check-prerequisites --json`.
    - `ok: true` → proceed.
    - `checksums_mismatch` → **HALT**. Report: "Engine integrity failure. Run `update-engine-meta` or restore from origin."
    - Missing `.design/` → auto-run `.magic/init.md`, then resume.
    - Apply Depth Control (Invariant 6): count source files and HALT per thresholds before scanning.
1. Build full project map.
2. Inferred stack + architecture style.
3. **Proposal**: Table of paired L1/L2 specs + RULES.md entries. Present with explicit options: **(a) Approve all** — dispatch all proposed specs and rules, **(b) Select** — user picks individual items to approve, **(c) Adjust** — user requests modifications to the proposal, **(d) Cancel** — discard the proposal entirely. Wait for user choice before proceeding.
4. **Registry Healing Guard**: If `INDEX.md` is blank/corrupted or mismatches the content of `specifications/` (Ghost/Zombie entries) → Prioritize **Registry Healing**: automatically re-map disk files to the registry and fix orphan paths before proposing new content.
5. **Advisory**: Generate Advisory Report (see §Advisory Report) for the analyzed scope.

### [Mode B] Re-Analysis (Delta Mode)

*Trigger: INDEX.md has active specs.*

0. **Pre-flight**: `node .magic/scripts/executor.js check-prerequisites --json`.
    - `ok: true` → proceed.
    - `checksums_mismatch` → **HALT**. Report: "Engine integrity failure. Run `update-engine-meta` or restore from origin."
    - Missing `.design/` → auto-run `.magic/init.md`, then resume.
    - Apply Depth Control (Invariant 6): count source files and HALT per thresholds before scanning.
1. Read existing specs; extract currently described paths/logic.
2. Scan actual project; build delta.
3. **Gap Report**:
    - **Covered**: Specs match code.
    - **Uncovered**: Code found without spec coverage.
    - **Orphaned**: Spec refers to deleted code.
    - **Drifted**: Spec structure differs from code.
    - **RESCUE (AOP)**: Name, title, or semantic similarity >80% → Propose rename/sync. If structural similarity <50% despite path correlation → Treat as **Uncovered** (New Spec) + **Orphaned** (Delete Old Spec).
    - **Logic Evolution**: If code structure/logic inside covered directories has structurally drifted (e.g., >30% new sub-modules, API schema shift) → **Propose Reality Sync**: Generate a structured diff or a "New Draft" version of the specification that reflects the actual codebase implementation. If approved: dispatch via `spec.md` Amendment Rule (Stable → RFC). C12 cascade applies to all L2 dependents of the affected spec.
4. **Advisory**: Generate Advisory Report (see §Advisory Report) for the analyzed scope.

### [Mode C] Project Ventilation

*Trigger*: `/magic.analyze`, `/magic.analyze {workspace}`, "Ventilate", "Ventilate {workspace}"
*Examples*: `/magic.analyze`, `/magic.analyze installers`, "Ventilate installers"

> **Mode Precedence**: When `/magic.analyze` is triggered and `INDEX.md` is empty, run Mode C first (self-check + registry audit). After the Mode C report is delivered, offer to continue with Mode A (first-time analysis) to generate initial spec proposals. Do NOT auto-start Mode A — the user may only want the audit.
> **Audit Policy**: This mode collects ALL issues (Drift, Gaps, Violations) before reporting. Bypassed HALT conditions in this mode: `checksums_mismatch`, Existence Guard, `VERSION_DRIFT`, C12 Quarantine. Report-delivery is the only HALT point.

1. **Self-Check**: Compare `.magic/` vs `.checksums`. (Non-halting audit).
2. **Registry Audit**: Cross-reference `INDEX.md` list vs actual files in `specifications/`. Use **exact string match** for filenames (not OS file-exists resolution) — a case mismatch (e.g., `API-Routes.md` on disk vs `api-routes.md` in INDEX) is a registry violation even on case-insensitive filesystems.
3. **Structural Integrity** (when workspace is specified):
    - Verify workspace folder exists at `.design/{workspace}/`.
    - Required contents: `INDEX.md`, `specifications/` directory.
    - Optional contents: `RULES.md` (workspace-scoped rules).
    - Cross-check `workspace.json` entry: `scope` paths exist on disk, `name` matches folder.
    - File naming: all spec files in `specifications/` follow kebab-case convention.
    - Cross-references: every spec listed in workspace `INDEX.md` has a corresponding file and vice versa.
    - **Report violations as `STRUCTURE` category** (separate from Drift/Gap/Orphan).
4. **Coverage Check**: Scan project directories *within the active workspace scope (C15)*. Identify folders with NO corresponding spec file (Gap Report).
    - **RESCUE (AOP)**: For each orphaned spec + uncovered directory pair, check name, path, title, or semantic similarity. If overall similarity >80%, classify as `RESCUE` (rename opportunity) instead of separate Gap + Orphan entries.
5. **Scope Blind-Spot Check** (multi-workspace projects): Compare the union of all workspace `scope` arrays against top-level project directories. Report any directories not covered by any workspace as `UNSCOPED` warnings: "Directory '{dir}' is not in any workspace scope — invisible to scoped analysis. Consider adding a workspace or extending an existing scope."
6. **Rule Validation**: Check `RULES.md §7` compliance (e.g., C15 adapter registry check).
7. **Auto-Repair suggest**: Suggest commands for missing specs, registry cleanup, or **Task Sync** (if C12 quarantine is triggered).
8. **Report**: Consolidated list of errors, warnings, and suggested repairs.
9. **Advisory**: Generate Advisory Report (see §Advisory Report) for the audited scope.

### [Mode D] Focused Analysis

*Trigger: Text argument provided (quoted string or non-workspace token).*
*Examples*: `/magic.analyze "проверь покрытие API"`, `/magic.analyze engine "фокус на тестах"`

> **Scope**: If a workspace is also specified, focus is applied within that workspace's scope. Otherwise, focus applies **project-wide** (C15 scope not enforced — the focus directive itself acts as the scan boundary).
> **Depth Control**: Exempt — targeted scan is narrow by definition. If focus resolves to >500 matched files, fall back to Invariant 6 thresholds.

1. **Parse Focus Directive**: Extract the intent from the text argument (area, layer, concern).
2. **Targeted Scan**: Instead of full project scan, narrow to directories/files relevant to the focus:
    - Match focus keywords against folder names, spec titles, module names, config sections.
    - If no matches found → **HALT**: "Could not map focus '{text}' to any project area. Try narrowing with a workspace: `/magic.analyze {workspace} \"{text}\"`, or rephrase the focus."
3. **Focused Gap Report**: Same categories as Mode B (Covered/Uncovered/Orphaned/Drifted) but only for the matched area.
4. **Advisory**: Always include the Advisory Report (see below) scoped to the focus area.

## Advisory Report

*Appended to Mode A/B/C/D reports. Chat-only output — never written to files.*

> **Purpose**: Actionable recommendations beyond fix/repair. Helps the user improve spec quality, coverage strategy, and project structure.

### Categories

1. **Spec Quality**
    - Oversized specs (>300 lines) → suggest splitting into L1 + L2s.
    - Bare L1 without L2 children → suggest adding detail specs.
    - L2 specs with no parent L1 → suggest grouping under an umbrella.
    - Specs with empty or stub sections → flag as incomplete.

2. **Coverage Strategy**
    - High-churn directories (≥10 commits in the last 30 days) without specs → prioritize coverage.
    - Test directories without corresponding test-suite spec → suggest `test-suite.md`.
    - Config-heavy areas (CI/CD, infra) without operational specs → suggest ops specs.

3. **Structural Improvements**
    - Workspace candidates: independent subdirectories that could benefit from their own workspace.
    - Rule consolidation: repeated patterns across workspace RULES.md → suggest promoting to global §6.
    - Naming inconsistencies: spec filenames that don't match their title or covered module.

4. **Action Proposals**
    - Each advisory item ends with a concrete next step:
      - `→ /magic.spec create {name}` for missing specs.
      - `→ /magic.spec amend {name}` for outdated specs.
      - `→ /magic.rule add "{convention}"` for uncodified patterns.
      - `→ /magic.analyze {workspace}` for deeper focused checks.
    - User approves/rejects each proposal individually. Approved items dispatch immediately.

### Output Format (Chat)

```
## 📋 Advisory Report

### Spec Quality
- ⚠ `engine-core.md` (342 lines) — consider splitting into focused L2 specs
  → /magic.spec create engine-core-lifecycle
  → /magic.spec create engine-core-invariants

### Coverage Strategy
- 💡 `scripts/` has 12 files, 47 recent commits, no spec coverage
  → /magic.spec create engine-scripts

### Structural Improvements
- 🔧 Workspace `installers` RULES.md repeats 3 rules from global §6
  → /magic.rule promote "C15 scope isolation"

### No Action Needed
- ✅ All L1 specs have L2 children
- ✅ Naming conventions consistent across workspaces
```

## Reporting & Dispatch

### Proposal Template (Artifact)

- **Stack/Arch**: Detected style + confidence.
- **Spec Matrix**: `# | Proposed Spec | Layer | Based On`.
- **Rules Matrix**: `# | Convention | Source`.

### Dispatch Logic (Approved)

1. **Specs**: Call `spec.md` "Creating a New Specification" (direct to Stable).
2. **Rules**: Apply via T4 protocol to `RULES.md §7`.
3. **Dispatch**:
    - Registry Sync: Update `INDEX.md`. Bump Registry version.
    - Post-Update Review: Run on all created specs before closing.
    - Context Regeneration: Run `node .magic/scripts/executor.js generate-context`.
    - **Actionable Outcome**: After silent dispatch, show: `[Auto-Analyze] {N} specs proposed and created as Stable.`

## Task Completion Checklist

```
Analysis Checklist — Mode A/B
  ☐ Depth Control obeyed; size-assessed before scanning
  ☐ Stack/Arch inferred; modules identified
  ☐ Mode correct (Analysis vs Re-Analysis Gap Report)
  ☐ RESCUE logic applied for renamed directories
  ☐ Dispatch: approved items created as Stable; RULES.md §7 updated
  ☐ Advisory Report appended to output
  ☐ Engine Meta: C14 bump if .magic/ files modified

Analysis Checklist — Mode C: Ventilation
  ☐ Self-check complete: engine integrity status noted (non-halting)
  ☐ Registry audit: orphans and unregistered files identified
  ☐ Structural Integrity checked (if workspace specified)
  ☐ Coverage check: gaps and RESCUE opportunities reported (scope-bounded by C15)
  ☐ Rule validation: RULES.md §7 compliance checked
  ☐ Report delivered: all findings consolidated before any HALT
  ☐ Advisory Report appended to output
  ☐ Engine Meta: C14 not triggered (Mode C is read-only — C1 §7)

Analysis Checklist — Mode D: Focused
  ☐ Focus directive parsed and matched to project area
  ☐ Targeted scan completed (not full project)
  ☐ Focused Gap Report generated for matched area only
  ☐ Advisory Report scoped to focus area
  ☐ Engine Meta: C14 not triggered (Mode D is read-only)
```
