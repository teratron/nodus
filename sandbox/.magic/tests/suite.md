# Workflow Test Suite

**Version:** 1.9.45
**Purpose:** Regression testing for Magic SDD engine workflows.
**Trigger:** `/magic.simulate test`

## How to Run

The agent reads this file, simulates each test scenario against the target workflow's logic, and reports PASS/FAIL for each expected outcome. No real files are created — all state is synthetic.

### Pass Criteria

A test **passes** if the workflow logic (as written in `.magic/*.md`) would produce the expected outcome given the synthetic state. A test **fails** if:

- A required guard is missing or would not trigger.
- The workflow would produce an incorrect or undefined result.
- An edge case is silently ignored instead of flagged.

### Report Format

After all tests, present a summary table:

```
Workflow Test Suite — {date}

| ID | Workflow | Scenario | Result |
| :--- | :--- | :--- | :--- |
| T01 | init | Fresh cold start | ✅ PASS |
| T02 | init | Partial corruption | ❌ FAIL |
...

Total: {N} passed, {M} failed out of {T}
```

If any test fails, document the failure reason and propose a fix.

## Test Scenarios

### T01 — Fresh Init Cold Start

- **Workflow:** `init.md`
- **Synthetic State:**
  - `.design/` does not exist
  - `.magic/.checksums` is valid
  - No git repository (optional)
- **Action:** Calling workflow triggers init via `check-prerequisites → ok: false`
- **Expected:**
  - [ ] `node .magic/scripts/executor.js init` is called
  - [ ] Post-init verification checks all 5 artifacts: `INDEX.md`, `RULES.md`, `specifications/`, `tasks/`, `archives/tasks/`
  - [ ] Brief report: "SDD initialized — {date}"
  - [ ] Calling workflow continues after init
- **Guards tested:** Engine Integrity check, post-init verification (5 artifacts)

### T02 — Init Partial Corruption

- **Workflow:** `init.md`
- **Synthetic State:**
  - `.design/` exists
  - `RULES.md` exists, `INDEX.md` is missing
  - `specifications/` exists, `tasks/` is missing
- **Action:** check-prerequisites → `ok: false` (missing required files) → init triggered
- **Expected:**
  - [ ] Init script runs and creates only missing artifacts (INDEX.md, tasks/)
  - [ ] Existing RULES.md is NOT overwritten (idempotency)
  - [ ] Post-init verification confirms all 5 artifacts present
- **Guards tested:** Safe to Re-Run (idempotency), full verification

### T03 — Spec Dispatch Multi-Topic

- **Workflow:** `spec.md` (Dispatching from Raw Input)
- **Synthetic State:**
  - `.design/` initialized with 2 existing specs: `architecture.md` (Stable), `api.md` (Draft)
  - `RULES.md` v1.2.0 with C1–C6
- **Input:** `"We need JWT auth with Redis sessions. Also, the API must use REST only. And we should use shadcn for the UI."`
- **Expected:**
  - [ ] Parse: 3 distinct topics identified
  - [ ] Map: JWT+Redis → `architecture.md`, REST → `architecture.md`, shadcn → new `ui-components.md`
  - [ ] Trust Mode (C9): No objective conflicts → mapping shown as "Notice of Intent", dispatch proceeds immediately
  - [ ] New file `ui-components.md` created from `.magic/templates/spec.md`
  - [ ] INDEX.md updated with new entry
  - [ ] Post-Update Review runs on all modified files
  - [ ] Actionable Outcome shown: `[Auto-SDD] {Spec} promoted to Stable; updated registry.`
- **Guards tested:** Multi-topic dispatch, Trust Mode auto-confirm, new file creation with template, registry sync

### T04 — Spec Intra-Input Self-Contradiction

- **Workflow:** `spec.md` (Dispatching from Raw Input)
- **Synthetic State:**
  - `.design/` initialized, `api.md` (Stable)
- **Input:** `"All APIs must use GraphQL. Also, REST is mandatory for mobile. And we plan to remove REST entirely in 2 months."`
- **Expected:**
  - [ ] Parse: 3 topics, all mapped to `api.md`
  - [ ] **Self-contradiction detected** before dispatch (GraphQL mandatory + REST mandatory + REST removal)
  - [ ] Agent flags all internal conflicts
  - [ ] Agent asks user to resolve before mapping — does NOT guess precedence
  - [ ] No writes occur until user resolves
- **Guards tested:** Intra-input self-contradiction edge case

### T05 — Spec Deprecation Cascade

- **Workflow:** `spec.md` (Updating an Existing Specification)
- **Synthetic State:**
  - `architecture.md` (Stable L1), `api.md` (Stable L2, Implements: architecture.md)
  - `database.md` (Stable L1, Related Specifications: api.md)
  - `PLAN.md` Phase 2: 4 tasks referencing `api.md`
- **Action:** User says: "Deprecate api.md"
- **Expected:**
  - [ ] Status change: `api.md` → Deprecated
  - [ ] INDEX.md updated: api.md status = Deprecated
  - [ ] **Deprecation Cascade**: `database.md` flagged as containing stale `Related Specifications` link to `api.md`
  - [ ] Post-Update Review surfaces stale references
- **Guards tested:** Deprecation Cascade (scan Related Specs)

### T06 — Task New Plan from Stable Specs

- **Workflow:** `task.md` (Generating Tasks & Plan)
- **Synthetic State:**
  - 3 Stable specs: `auth.md` (L1) → `auth-impl.md` (L2, Implements: auth.md) → `api.md` (L1, unrelated)
  - No PLAN.md, no TASKS.md
  - RULES.md does not contain execution mode
- **Expected:**
  - [ ] All 3 specs read, dependency graph built
  - [ ] Phases proposed: auth.md (L1) → Phase 0/1, auth-impl.md (L2) → Phase 1/2, api.md (L1) → Phase 0/1
  - [ ] L2 spec scheduled AFTER its L1 parent
  - [ ] Execution mode asked (since not in RULES.md §7)
  - [ ] Mode saved to RULES.md §7 on user answer
  - [ ] PLAN.md created from `.magic/templates/plan.md`
  - [ ] TASKS.md + phase-1.md created from `.magic/templates/tasks.md`
- **Guards tested:** Dependency ordering, layer respect, template usage, mode persistence

### T07 — Task Circular Dependency

- **Workflow:** `task.md` (Generating Tasks & Plan)
- **Synthetic State:**
  - `auth.md` (Stable, Related: api.md)
  - `api.md` (Stable, Related: auth.md)
  - Circular dependency: auth → api → auth
- **Expected:**
  - [ ] Dependency graph construction detects cycle
  - [ ] **HALT** — cycle flagged to user
  - [ ] Proposal: break cycle by removing one Related Specifications link or splitting spec
  - [ ] No PLAN.md written until cycle resolved
- **Guards tested:** Circular Dependency Guard

### T08 — Task Phantom Specs with Done Tasks

- **Workflow:** `task.md` (Updating Tasks & Plan)
- **Synthetic State:**
  - INDEX.md: `auth.md` (Stable), `api.md` (Stable)
  - PLAN.md references `auth.md`, `api.md`, and `secrets.md` (phantom — not in INDEX.md)
  - TASKS.md: T-1A01 (secrets.md, Done), T-1A02 (secrets.md, In Progress), T-1B01 (auth.md, Todo)
- **Expected:**
  - [ ] `secrets.md` flagged as Phantom Spec
  - [ ] T-1A01 (Done) → preserved as Archived Orphan (history intact)
  - [ ] T-1A02 (In Progress) → marked Cancelled (Reason: Phantom Spec)
  - [ ] T-1B01 (auth.md, Todo) → unaffected
  - [ ] Done work is NOT cancelled
- **Guards tested:** Phantom spec Done-task preservation

### T09 — Run Sequential Happy Path

- **Workflow:** `run.md` (Executing Tasks — Sequential Mode)
- **Synthetic State:**
  - TASKS.md: Phase 1, 3 tasks (T-1A01 Todo, T-1A02 Todo dep:T-1A01, T-1A03 Todo dep:T-1A02)
  - RULES.md §7 C3: Sequential mode
  - All spec files exist
- **Expected:**
  - [ ] Pre-flight: check-prerequisites → ok
  - [ ] Mode Guard: Sequential found in RULES.md §7 → proceed
  - [ ] T-1A01 picked (no deps), executed, marked Done
  - [ ] T-1A02 unblocked, picked next
  - [ ] On phase complete: retrospective Level 1 auto-snapshot
  - [ ] Changelog Level 1 compiled to CHANGELOG.md
  - [ ] Phase file archived to `archives/tasks/`
- **Guards tested:** Dependency chain, auto-snapshot, changelog, archival

### T10 — Run Mode Not in RULES.md

- **Workflow:** `run.md` (Executing Tasks)
- **Synthetic State:**
  - TASKS.md exists with Phase 1 tasks
  - RULES.md §7 does **not** contain execution mode convention
- **Expected:**
  - [ ] Pre-flight: check-prerequisites → ok
  - [ ] Mode Guard: execution mode NOT found in RULES.md §7
  - [ ] **HALT** — agent does NOT assume Sequential or Parallel
  - [ ] Message: "Execution mode is not defined. Please run `magic.task` first."
  - [ ] No task execution begins
- **Guards tested:** Mode Guard (HALT on missing mode)

### T11 — Run Full Deadlock (100% Blocked)

- **Workflow:** `run.md` (Executing Tasks — Sequential Mode)
- **Synthetic State:**
  - Phase 2: 4 tasks, all status = Blocked
  - Phase 1: all Done (archived)
  - RULES.md §7 C3: Sequential mode
- **Expected:**
  - [ ] Pre-flight passes
  - [ ] Find next Todo task → none found
  - [ ] Stalled Phase detected: Blocked tasks remain but no Todo
  - [ ] Agent reports stall with summary of blocked items
  - [ ] Agent does NOT loop — escalates to user and waits
- **Guards tested:** Stalled Phase escalation, no infinite loop

### T12 — Rule Add Duplicate Convention

- **Workflow:** `rule.md` (Adding a Convention)
- **Synthetic State:**
  - RULES.md §7 contains C5: "All dates use ISO 8601 format."
- **Input:** `"Add rule: dates must follow ISO 8601."`
- **Expected:**
  - [ ] Pre-flight passes
  - [ ] RULES.md read in full
  - [ ] **Duplication Guard**: semantic overlap with C5 detected
  - [ ] Agent shows existing C5 and asks: "This overlaps with C5. Merge, replace, or add separately?"
  - [ ] No write occurs until user decides
- **Guards tested:** Duplication Guard

### T13 — Rule Remove with Workflow Dependency

- **Workflow:** `rule.md` (Removing a Convention)
- **Synthetic State:**
  - RULES.md §7 C3: "Parallel Task Execution Mode"
  - `run.md` references C3 via Mode Guard
- **Input:** `"Remove rule C3"`
- **Expected:**
  - [ ] Pre-flight passes
  - [ ] Target identified: C3 — Parallel Task Execution Mode
  - [ ] Removal proposed with major version bump
  - [ ] **Workflow Dependency Check**: C3 is referenced by `run.md` as Mode Guard
  - [ ] Warning: "This rule is used by run.md as Mode Guard. Removing it may break that workflow's logic."
  - [ ] Impact Analysis includes TASKS.md version staleness note
- **Guards tested:** Workflow Dependency Check, Impact Analysis

### T15 — Retrospective Level 1 Auto-Snapshot (RETRO Missing)

- **Workflow:** `retrospective.md` (Level 1: Auto-Snapshot)
- **Synthetic State:**
  - Phase 1 just completed (all tasks Done)
  - INDEX.md: 3 specs (1 Draft, 1 RFC, 1 Stable)
  - TASKS.md: 5 Done, 0 Blocked
  - RULES.md §7: 4 entries
  - `RETROSPECTIVE.md` does NOT exist
- **Expected:**
  - [ ] Pre-flight passes
  - [ ] INDEX.md read: D/R/S = 1/1/1
  - [ ] TASKS.md summary: 5 Done, 0 Blocked
  - [ ] RULES.md §7: 4 entries counted
  - [ ] Signal: 🟢 (0 Blocked, 100% coverage)
  - [ ] RETROSPECTIVE.md created from `.magic/templates/retrospective.md`
  - [ ] Snapshot row appended (Snapshots section only — no Session for Level 1)
  - [ ] Phase file archived to `archives/tasks/`
- **Guards tested:** Template creation on missing file, signal calculation, archival

### T16 — Simulate Checksums Mismatch HALT

- **Workflow:** `simulate.md` (Step 0: Pre-flight)
- **Synthetic State:**
  - `.magic/.checksums` exists
  - `spec.md` hash does not match stored checksum (file was modified without regeneration)
- **Action:** `/magic.simulate spec`
- **Expected:**
  - [ ] check-prerequisites reports `checksums_mismatch` for `spec.md`
  - [ ] **HALT** — do NOT proceed with simulation
  - [ ] Report mismatched files to user
  - [ ] **Hint Provided**: Agent suggests `update-engine-meta --workflow {wf}` to restore integrity.
  - [ ] Options: confirm changes were intentional (sync meta) OR restore from origin.
  - [ ] Simulation resumes only after user response
- **Guards tested:** Checksums mismatch HALT (Step 0)

### T17 — Spec T4 Trigger (Auto Rule Capture)

- **Workflow:** `spec.md` (T4: Rule Extraction)
- **Synthetic State:**
  - `.design/` initialized, `api.md` (Stable)
  - RULES.md §7: C1–C6, no API convention
- **Input:** `"From now on, all APIs must use gRPC. Add this to the API spec."`
- **Expected:**
  - [ ] T4 trigger detected: "from now on" is a standing-rule signal
  - [ ] Agent writes spec changes AND proposes new §7 convention
  - [ ] Convention proposed: `C7 — gRPC-Only API Standard`
  - [ ] User asked to approve the rule before writing to RULES.md
  - [ ] If approved: RULES.md §7 updated, version bumped
  - [ ] `api.md` updated with gRPC requirement
- **Guards tested:** T4 standing-rule detection, dual write (spec + rule)

### T18 — Spec Explore Mode to Formal Spec

- **Workflow:** `spec.md` (Explore Mode → Formal Spec)
- **Synthetic State:**
  - `.design/` initialized, no existing specs
- **Input:** `"Let's brainstorm about authentication approaches"` → then `"OK, let's formalize the OAuth2 approach"`
- **Expected:**
  - [ ] Phase 1 (explore): agent outputs thoughts to chat or creates a temporary proposal in the agent's artifacts directory (never in `.design/`)
  - [ ] No INDEX.md entry during explore (safety)
  - [ ] No status lifecycle applied during explore
  - [ ] No `.design/specifications/`, `INDEX.md`, `PLAN.md`, or `TASKS.md` modifications during explore
  - [ ] Phase 2 (formalize): agent creates `.design/specifications/auth.md` from template
  - [ ] INDEX.md updated with auth.md (Draft)
- **Guards tested:** Explore Mode isolation (no `.design/` writes), transition to formal, template usage

### T19 — Spec Update Stable → RFC (Amendment Rule)

- **Workflow:** `spec.md` (Updating an Existing Specification)
- **Synthetic State:**
  - `auth.md` (Stable, v2.0.0) with existing implementation tasks
  - User wants to add a major new section (2FA support)
- **Input:** `"Add two-factor authentication support to auth spec"`
- **Expected:**
  - [ ] Change scope assessed: new section → minor bump (v2.1.0)
  - [ ] Status reverts: Stable → RFC (amendment rule triggered)
  - [ ] INDEX.md updated: status = RFC, version = 2.1.0
  - [ ] Document History row appended
  - [ ] Post-Update Review runs
  - [ ] RULES.md triggers evaluated
- **Guards tested:** Amendment rule (Stable→RFC on substantive change), version bump

### T20 — Run Parallel Mode (2 Tracks, Shared Conflict)

- **Workflow:** `run.md` (Executing Tasks — Parallel Mode)
- **Synthetic State:**
  - TASKS.md Phase 1: Track A (T-1A01 Todo, T-1A02 Todo) + Track B (T-1B01 Todo)
  - T-1A02 and T-1B01 both modify `shared-config.md`
  - RULES.md §7 C3: Parallel mode
- **Expected:**
  - [ ] Pre-flight passes
  - [ ] Mode Guard: Parallel found → Manager Agent activated
  - [ ] T-1A01 and T-1B01 started in parallel (no shared constraints)
  - [ ] T-1A02 flagged: shared constraint with T-1B01 on `shared-config.md`
  - [ ] Manager serializes conflicting tasks (one waits for the other)
  - [ ] No data loss or race condition
- **Guards tested:** Parallel execution, shared-constraint detection, Manager serialization

### T21 — Run Full Plan Complete (Conclusion Cascade)

- **Workflow:** `run.md` + `retrospective.md` (Plan Completion)
- **Synthetic State:**
  - TASKS.md: Phase 1 Done (archived), Phase 2 Done (last phase)
  - All specs implemented, all tasks Done
  - RULES.md §7 C3: Sequential mode
- **Expected:**
  - [ ] Phase 2 completion detected → Level 1 retro auto-snapshot
  - [ ] **Full plan completion** detected → Level 2 retrospective triggered
  - [ ] Level 2 retro: structured analysis with metrics across all phases
  - [ ] Changelog Level 2 compiled (requires user approval before writing)
  - [ ] CONTEXT.md regenerated
  - [ ] TASKS.md summary updated
- **Guards tested:** Plan completion detection, Level 2 retro trigger, changelog approval gate

### T22 — Run Phase 1→2 Transition

- **Workflow:** `run.md` (Phase Transition)
- **Synthetic State:**
  - Phase 1: all tasks Done
  - Phase 2: 4 tasks Todo, not yet started
  - RULES.md §7 C3: Sequential mode
- **Expected:**
  - [ ] Phase 1 completion detected
  - [ ] Level 1 retro auto-snapshot fires
  - [ ] Phase 1 file archived: `tasks/ → archives/tasks/` (C8)
  - [ ] TASKS.md link updated to archive location
  - [ ] Agent transitions to Phase 2: reads `phase-2.md`
  - [ ] First Todo task in Phase 2 picked automatically
  - [ ] No user prompt between phases (C9: Zero-Prompt Automation)
- **Guards tested:** Phase archival (C8), seamless transition, Zero-Prompt (C9)

### T23 — Retrospective Level 2 Full Analysis

- **Workflow:** `retrospective.md` (Level 2: Full Retrospective)
- **Synthetic State:**
  - 3 phases completed (all archived)
  - Phase 1: 5 tasks (4 Done, 1 Cancelled), bottleneck: external API delay
  - Phase 2: 8 tasks (7 Done, 1 Blocked→Done), slow track B
  - Phase 3: 3 tasks (all Done), smooth execution
  - RETROSPECTIVE.md exists with 3 Level 1 snapshots
- **Expected:**
  - [ ] All 3 snapshots read and analyzed
  - [ ] Cross-phase metrics: completion rates, bottleneck patterns
  - [ ] Trends: improving velocity Phase 1→3
  - [ ] Recommendations section generated
  - [ ] Session entry appended to RETROSPECTIVE.md (not snapshot)
  - [ ] User asked: "Generate external changelog?" (Level 2 approval gate)
- **Guards tested:** Multi-phase analysis, trend detection, approval gate for Level 2 changelog

### T24 — Task Selective Planning (C6) with Mixed Statuses

- **Workflow:** `task.md` (Updating Tasks & Plan)
- **Synthetic State:**
  - INDEX.md: 10 specs total — 3 Draft, 4 RFC, 3 Stable
  - No existing PLAN.md
  - RULES.md §7: C6 active
- **Expected:**
  - [ ] 3 Draft specs → automatically moved to `## Backlog` in PLAN.md (no prompt — C6)
  - [ ] 4 RFC specs → automatically moved to `## Backlog` in PLAN.md (no prompt — C6)
  - [ ] 3 Stable specs → all automatically pulled into active plan phases (no user choice — C6)
  - [ ] PLAN.md contains phases covering all 3 Stable specs
  - [ ] All Draft and RFC in Backlog, not in active phases
  - [ ] No Draft/RFC spec enters active phases without explicit pull
- **Guards tested:** Selective Planning (C6), mixed status handling, zero-prompt automation

### T25 — Rule Amend Core Section (§1–6)

- **Workflow:** `rule.md` (Amending a Convention)
- **Synthetic State:**
  - RULES.md: §2 Status Rules contain `RFC → Stable: reviewed, approved, no open questions.`
- **Input:** `"Change rule: RFC specs can go Stable with one approval instead of full review"`
- **Expected:**
  - [ ] Agent identifies target: §2 (core section, not §7)
  - [ ] Convention-not-found in §7 handler triggers
  - [ ] Agent informs: "This is a core section (§2). Amending requires explicit approval."
  - [ ] Constitutional implications surfaced: relaxing quality gate
  - [ ] User must explicitly confirm core amendment
  - [ ] If approved: §2 updated, RULES.md major version bump
- **Guards tested:** Convention-not-found handler, core section amendment gate

### T27 — Spec Full Consistency Audit

- **Workflow:** `spec.md` (Consistency Check & Audit Report)
- **Synthetic State:**
  - INDEX.md: 6 specs registered
  - `.design/specifications/`: 7 files (1 unregistered: `orphan.md`)
  - `api.md` lists `Related: legacy.md` but `legacy.md` status = Deprecated
  - `auth-impl.md` (L2) has `Implements: auth.md`, but `auth.md` is Draft (not Stable)
  - `ui.md` version in file = 2.1.0, version in INDEX.md = 1.5.0
- **Expected:**
  - [ ] Orphaned file detected: `orphan.md` in filesystem but not in INDEX.md
  - [ ] Stale reference: `api.md` → `legacy.md` (Deprecated) flagged
  - [ ] Layer violation: `auth-impl.md` (L2) references non-Stable L1 parent
  - [ ] Version mismatch: `ui.md` file vs INDEX.md discrepancy flagged
  - [ ] Consistency Report generated with all 4 issues
  - [ ] No automatic fixes — all surfaced for user decision
- **Guards tested:** Orphan detection, stale refs, layer integrity, version sync

### T28 — End-to-End Lifecycle (Cross-Workflow Chain)

- **Workflow:** `init.md` → `spec.md` → `task.md` → `run.md` → `retrospective.md`
- **Synthetic State:**
  - Clean project, no `.design/` directory
- **Action:** User says: "I want to build a REST API for user management"
- **Expected:**
  - [ ] **init**: `.design/` created, INDEX.md + RULES.md initialized
  - [ ] **spec**: `user-management-api.md` created from template, registered in INDEX.md (Draft)
  - [ ] **spec update**: Status promoted Draft → RFC → Stable (with user confirmations)
  - [ ] **task**: Dependency graph built (1 spec), PLAN.md created (1 phase), TASKS.md created
  - [ ] **task**: Execution mode asked and saved to RULES.md §7
  - [ ] **run**: Mode Guard passes, tasks executed sequentially
  - [ ] **run**: Phase completed, Level 1 retro fires
  - [ ] **run**: Plan completed, Level 2 retro fires
  - [ ] **retrospective**: RETROSPECTIVE.md created, snapshot + session appended
  - [ ] All files consistent: INDEX.md, PLAN.md, TASKS.md, RULES.md in sync
  - [ ] No orphaned specs, no stale references, no version mismatches
- **Guards tested:** Full chain integrity, all workflow handoffs, all guards in sequence

### T29 — Analyze First-Time on Existing Project

- **Workflow:** `analyze.md` (First-Time Analysis, delegated from `spec.md`)
- **Synthetic State:**
  - `.design/` initialized (INDEX.md exists, empty — 0 specs registered)
  - Project has: `package.json` (Next.js), `src/` with `components/`, `pages/`, `api/`, `lib/`
  - `.eslintrc.json`, `tsconfig.json`, `tailwind.config.js` exist
  - ~80 source files total
- **Action:** User says: "Analyze this project"
- **Expected:**
  - [ ] `spec.md` Explore Mode triggered → delegation rule fires → `analyze.md` read
  - [ ] INDEX.md empty → First-Time Analysis mode selected (not Re-Analysis)
  - [ ] Step 1: Structure scan identifies `src/components/`, `src/pages/`, `src/api/`, `src/lib/`
  - [ ] Step 2: Stack detected — Next.js + TypeScript + Tailwind
  - [ ] Step 3: Architecture inferred — Frontend SPA (pages/ + components/) with API routes
  - [ ] Step 4: Conventions detected from `.eslintrc.json`, `tsconfig.json`
  - [ ] Step 5: Proposal generated to **agent artifacts** (NOT `.design/`)
  - [ ] Proposal contains: ≥3 proposed L1 specs, ≥3 proposed L2 specs, ≥1 RULES.md §7 convention
  - [ ] Step 6: User prompted with options (Approve all / Select / Adjust / Cancel)
  - [ ] No `.design/specifications/` files created until approval
- **Guards tested:** Delegation routing, First-Time detection, read-only scan, Explore Mode safety (no live writes)

### T30 — Analyze Re-Analysis Gap Detection

- **Workflow:** `analyze.md` (Re-Analysis Mode, delegated from `spec.md`)
- **Synthetic State:**
  - `.design/INDEX.md`: 3 specs registered:
    - `architecture.md` (Stable L1) — describes `src/core/`, `src/api/`
    - `auth.md` (Stable L1) — describes `src/auth/`
    - `database.md` (Stable L1) — describes `src/db/`
  - **Actual project structure:**
    - `src/core/` → exists (covered ✅)
    - `src/auth/` → renamed to `src/authentication/` (drifted 🔄)
    - `src/db/` → deleted, replaced by `src/database/` (drifted 🔄)
    - `src/payments/` → new module, no spec (uncovered ⚠️)
    - `src/notifications/` → new module, no spec (uncovered ⚠️)
- **Action:** User says: "Re-analyze the project"
- **Expected:**
  - [ ] INDEX.md read → 3 active specs found → Re-Analysis Mode selected
  - [ ] Active specs read: paths and structures extracted
  - [ ] Project scanned: actual directories discovered
  - [ ] Delta computed:
    - `src/core/` → `architecture.md` ✅ Covered
    - `src/auth/` → `auth.md` 🔄 Drifted (renamed to `src/authentication/`)
    - `src/db/` → `database.md` 🔄 Drifted (renamed to `src/database/`)
    - `src/payments/` → ⚠️ Uncovered
    - `src/notifications/` → ⚠️ Uncovered
  - [ ] Gap Report generated to agent artifacts with L1/L2 paired Coverage Matrix
  - [ ] 2 new L1 specs proposed (`payments.md`, `notifications.md`) + 2 paired L2 specs
  - [ ] 2 spec updates proposed (path fixes in `auth.md`, `database.md`)
  - [ ] User prompted before any live modifications
- **Guards tested:** Re-Analysis mode detection, delta comparison, drift detection, uncovered module detection

### T31 — Analyze Delegation Routing from spec.md

- **Workflow:** `spec.md` → `analyze.md` (Delegation)
- **Synthetic State:**
  - `.design/` initialized, INDEX.md has 2 specs registered
  - Project has existing code
- **Test A — Analysis trigger:**
  - **Input:** `"Scan the project for uncovered modules"`
  - **Expected:**
    - [ ] `spec.md` Explore Mode entered
    - [ ] Delegation rule matches: "Scan ... modules" → `analyze.md`
    - [ ] `analyze.md` read and Re-Analysis flow executed
- **Test B — Generic brainstorm (no delegation):**
  - **Input:** `"Let's brainstorm about caching strategies"`
  - **Expected:**
    - [ ] `spec.md` Explore Mode entered
    - [ ] Delegation rule does NOT match (no project analysis intent)
    - [ ] Standard Explore Mode proceeds (thinking partner, no live writes)
- **Guards tested:** Delegation trigger accuracy, non-matching triggers stay in Explore Mode

### T32 — Init Existing Codebase Hint

- **Workflow:** `init.md` (Existing Codebase Hint)
- **Test A — Project with code:**
  - **Synthetic State:**
    - `.design/` does NOT exist
    - Project root has: `package.json`, `src/`, `README.md`, 20+ source files
  - **Action:** Any workflow triggers init
  - **Expected:**
    - [ ] Init runs: `.design/` created with all 5 artifacts
    - [ ] Post-init: codebase indicators scanned — `package.json` found
    - [ ] Hint appended: `💡 Existing codebase detected. To generate initial specifications from your code, say: "Analyze project"`
    - [ ] Calling workflow continues after hint
- **Test B — Empty project (no code):**
  - **Synthetic State:**
    - `.design/` does NOT exist
    - Project root has only `.magic/` (freshly installed magic-spec, no user code)
  - **Action:** Any workflow triggers init
  - **Expected:**
    - [ ] Init runs: `.design/` created with all 5 artifacts
    - [ ] Post-init: no codebase indicators found
    - [ ] **No hint** — analysis not suggested for empty projects
    - [ ] Calling workflow continues
- **Guards tested:** Codebase detection heuristic, hint presence/absence

### T33 — Analyze Depth Control for Large Projects

- **Workflow:** `analyze.md` (Depth Control)
- **Test A — Small project (<50 files):**
  - **Synthetic State:**
    - 30 source files, `.design/INDEX.md` empty
  - **Expected:**
    - [ ] Full scan starts automatically — no prompt
- **Test B — Medium project (50–500 files):**
  - **Synthetic State:**
    - 200 source files, `.design/INDEX.md` empty
  - **Expected:**
    - [ ] Agent offers: Full scan or Focused scan
    - [ ] Proceeds only after user choice
- **Test C — Large project (>500 files):**
  - **Synthetic State:**
    - 1200 source files across 80 directories, `.design/INDEX.md` empty
  - **Expected:**
    - [ ] Agent recommends Focused or Quick scan
    - [ ] Full scan offered as option but not default
    - [ ] Agent does NOT auto-start full scan on large projects
- **Guards tested:** Depth Control thresholds (<50, 50–500, >500), auto-scan vs prompt

### T34 — Simulate Missing Test Suite (Improv Mode Fallback)

- **Workflow:** `simulate.md` (Improv Mode)
- **Synthetic State:**
  - `.magic/tests/suite.md` file is missing or inaccessible.
- **Action 1:** User runs `/magic.simulate test`
- **Expected 1:**
  - [ ] Agent checks for `.magic/tests/suite.md` and fails to find it.
  - [ ] Agent alerts user that test suite is missing, provides hint to restore file from origin, and falls back to **Improv Mode**.
  - [ ] Agent synthesizes a complex "Crisis Scenario" (e.g., INDEX.md desync).
  - [ ] Agent runs an end-to-end simulated lifecycle (Spec → Task → Run → Retro).
  - [ ] Agent outputs a Friction Audit report with identified "Rough Edges".
- **Action 2:** User runs `/magic.simulate` (without target), user requests generic "live simulation"
- **Expected 2:**
  - [ ] Agent defaults to **Improv Mode**.
  - [ ] Executes the same synthesis and lifecycle end-to-end as Expected 1.
- **Guards tested:** Fallback trigger on missing tests, Improv Mode end-to-end execution, ambiguity handling

### T35 — Run Sequence Syncs to PLAN.md

- **Workflow:** `run.md` (Executing Tasks)
- **Synthetic State:**
  - `TASKS.md` Phase 1 has 2 tasks mapped to `auth.md`.
  - Both tasks are transition to marked `Done` after execution.
  - `PLAN.md` has `[ ] Implement Auth module` pointing to `auth.md` under Phase 1.
- **Action:** User says "Execute tasks"
- **Expected:**
  - [ ] Agent reads TASKS.md and identifies fully implemented spec (`auth.md`).
  - [ ] Agent modifies `.design/PLAN.md` to change `[ ]` to `[x]` for `auth.md`.
  - [ ] TASKS.md updated with `Done`.
- **Guards tested:** Plan Sync mechanism (Plan Amnesia fix)

### T36 — Run Task Blocked Handoff to spec.md

- **Workflow:** `run.md` (Executing Tasks)
- **Synthetic State:**
  - `TASKS.md` Phase 2 has 1 active task mapped to `auth.md`.
  - Task execution encounters ambiguous or missing details in the specification.
- **Action:** User executes `/magic.run`
- **Expected:**
  - [ ] Agent records `Blocked` status and the specific reason in `TASKS.md` Notes.
  - [ ] Agent utilizes the newly added `magic.spec` handoff in `.agent/workflows/magic.run.md`.
  - [ ] Agent delegates resolution to `magic.spec` workflow (Explore/Update Mode).
  - [ ] Once the specification is formally updated and unblocked, agent proceeds to `magic.task` to rebuild task dependencies.
- **Guards tested:** Cross-workflow handoff routing, blocked task escalation.

### T37 — Simulate Regression Sweep Post-Fix

- **Workflow:** `simulate.md` (Verification Step)
- **Synthetic State:**
  - Logic flaw found in a workflow definition (e.g. `init.md`).
  - Surgical fix applied.
  - Test case appended to `suite.md`.
- **Action:** User explicitly approves the "Corrective Proposal" changes.
- **Expected:**
  - [ ] Agent performs a spot-check of the modified lines in `init.md`.
  - [ ] Agent explicitly utilizes the *Run regression tests* handoff from `.agent/workflows/magic.simulate.md` or directly triggers the `/magic.simulate test` suite.
  - [ ] Full regression suite is executed sequentially to ensure core `init.md` modifications did not break adjacent workflows.
- **Guards tested:** Post-fix regression sweep enforcement.

### T38 — Workspace Context Resolution (Zero-Prompt)

- **Workflow:** Any (`task.md` used as example)
- **Synthetic State:**
  - `.design/workspace.json` exists with `{"default": "engine", "workspaces": {"engine": {}, "installers": {}}}`
  - No prompt provided by user about workspaces.
- **Action 1:** Workflow triggered with no environment variables or CLI flags.
- **Expected 1:**
  - [ ] Agent reads `.design/workspace.json`.
  - [ ] Agent silently identifies `default` = `engine`.
  - [ ] Agent uses `.design/engine/` for all file operations (reading `INDEX.md`, `RULES.md`, etc.).
  - [ ] User is NOT prompted to select a workspace.
- **Action 2:** Workflow triggered with `MAGIC_WORKSPACE=installers`
- **Expected 2:**
  - [ ] Agent silently uses `.design/installers/` (overriding default).
- **Action 3:** `.design/workspace.json` is deleted. Workflow triggered.
- **Expected 3:**
  - [ ] Fallback kicks in silently.
  - [ ] Agent uses root `.design/` for all operations.
- **Guards tested:** Context Resolution Priority, Zero-Prompt Enforcement, Graceful Fallback.

### T39 — Retrospective Path and Template Resilience

- **Workflow:** `retrospective.md`
- **Synthetic State:**
  - Workspace `installers` is active (`MAGIC_DESIGN_DIR=.design/installers/`).
  - `.design/installers/` initialized and Phase 1 just completed.
  - `RETROSPECTIVE.md` does NOT exist in `.design/installers/`.
- **Action:** Retrospective Level 1 triggered
- **Expected:**
  - [ ] Agent creates `/installers/RETROSPECTIVE.md` from `.magic/templates/retrospective.md` exactly as is without removing the "Session" sections.
  - [ ] Agent appends a row to the Snapshots table.
  - [ ] Agent archives the phase file purely relatively: `tasks/phase-1.md` → `archives/tasks/`
  - [ ] Agent does NOT write anything to `.design/` root.
- **Guards tested:** Workspace path adherence, Level 1 template fidelity.

### T40 — Analyze Auto-Init Guard and Markdown List Integrity

- **Workflow:** `analyze.md`
- **Synthetic State:** Fresh repository without `.design/` directory.
- **Action:** User prompts *"Analyze my codebase"* (triggers analyze).
- **Expected:**
  - [ ] Agent intercepts execution and triggers `.magic/init.md` pre-flight before scanning.
  - [ ] Agent processes all 7 Re-Analysis steps linearly without sequence restart.
- **Guards tested:** Auto-Init Delegation, Markdown List Continuity.

### T41 — Run Phase Completion with Cancelled Tasks Guard

- **Workflow:** `run.md` + `retrospective.md`
- **Synthetic State:**
  - `TASKS.md` summary table lists 3 `Done` and 1 `Cancelled` task.
  - Phase 1 has no `Todo` tasks and no `Blocked` tasks.
  - Entire plan only has Phase 1.
- **Action:** Agent marks the final available task as `Done`.
- **Expected:**
  - [ ] Agent recognizes Phase 1 is complete (condition: all `Done` or `Cancelled`).
  - [ ] Agent recognizes entirely plan is complete.
  - [ ] Retrospective and summary extract `Cancelled` metric successfully.
- **Guards tested:** Phase completion on Cancelled, Missing Cancelled Metric.

### T42 — Simulate Improv Mode Zero-Prompt Fallback

- **Workflow:** `simulate.md` (Wrapper & Engine)
- **Synthetic State:** Fresh design session, all files present.
- **Action:** User prompts `"/magic.simulate"` without arguments.
- **Expected:**
  - [ ] Agent reads `.agent/workflows/magic.simulate.md`.
  - [ ] Agent does NOT ask the user to "pick a workflow".
  - [ ] Agent explicitly engages Step 1.5 "Improv Mode (Live Simulation)".
  - [ ] Agent invents a crisis scenario and proceeds autonomously.
- **Guards tested:** Zero-prompt fallback rule, prompt ambiguity block.

### T43 — Rule Batch Operations and ID Assignment

- **Workflow:** `rule.md`
- **Synthetic State:**
  - `RULES.md` §7 currently has rules up to C3.
- **Action:** User prompts *"Amend C2 to say X, and add two new rules: Y and Z"*.
- **Expected:**
  - [ ] Agent groups the amendment and two additions into a SINGLE proposal block.
  - [ ] Agent asks for a single "Apply all?" confirmation.
  - [ ] New rules are accurately assigned sequential IDs by calculating highest existing (`C4` and `C5`).
  - [ ] Agent performs a single final version bump.
- **Guards tested:** Batch operations spam prevention, Dynamic ID assignment.

### T45 — Run Version Bleed Guard

- **Workflow:** `run.md`
- **Synthetic State:**
  - Entire plan is completed (Phase 2 done).
  - Node.js project. `package.json` exists with version `"1.0.0"`.
  - Level 2 Changelog approved.
- **Action:** User prompts to finish execution. Agent updates version.
- **Expected:**
  - [ ] Agent bumps version inside `package.json`.
  - [ ] Agent does NOT attempt to modify `.magic/.version` in any way.
- **Guards tested:** Version Bleed Prevention.

### T46 — Spec Rename Retention

- **Workflow:** `spec.md` & `task.md`
- **Synthetic State:**
  - Spec `auth-draft.md` is registered and partially completed in `PLAN.md` / `TASKS.md`.
- **Action:** User requests to rename `auth-draft.md` to `authentication.md`.
- **Expected:**
  - [ ] Agent performs a global search-and-replace across all `.design/` files.
  - [ ] Running `magic.task` after rename does NOT trigger a Phantom Spec reset.
  - [ ] Existing tasks in `TASKS.md` retain progress but point to the new spec name.
- **Guards tested:** Spec Renaming Protocol, Task Continuity.

### T47 — Stability Downgrade Tracking

- **Workflow:** `task.md`
- **Synthetic State:**
  - Spec `api.md` was `Stable` and has active tasks (`Done` and `Pending`).
  - The spec receives heavy modifications and is downgraded to `RFC`.
- **Action:** User runs `/magic.task` to update the plan.
- **Expected:**
  - [ ] Agent moves `api.md` to Backlog in `PLAN.md`.
  - [ ] Agent does NOT delete active tasks.
  - [ ] Pending tasks are marked `Blocked [!]` with "Awaiting spec stabilization".
- **Guards tested:** Stability Downgrade Guard, Backlog Placement, Active Task Preservation.

### T48 — Automation Handoff Validation (Init)

- **Workflow:** `init.md`
- **Synthetic State:**
  - `.design/` directory is missing.
  - Engine `.magic/.checksums` exists.
  - User edited `.magic/scripts/init.js` manually.
  - `check-prerequisites` JSON output contains `"warnings": ["Engine Integrity: '.magic/scripts/init.js' has been modified..."]`.
- **Action:** An arbitrary workflow calls `init.md` indirectly.
- **Expected:**
  - [ ] Agent reads the JSON output and detects the `Engine Integrity` warning.
  - [ ] Agent does **NOT** attempt to compute SHA256 hashes manually.
  - [ ] Agent HALTs initialization immediately and reports the mismatch.
- **Guards tested:** AOP Automation Delegation, Engine Integrity Guard.

### T49 — Analysis Depth Control (Prioritization)

- **Workflow:** `analyze.md`
- **Synthetic State:**
  - Project contains > 500 files.
  - No existing specs.
- **Action:** User runs command to analyze project.
- **Expected:**
  - [ ] Agent executes Step 0 (Size Assessment) *before* Step 1.
  - [ ] Agent detects `> 500 files` using an optimal scanning command (`list_dir`, `find`, or OS equiv).
  - [ ] Agent halts and asks the user for scanning scope (Full, Focused, or Quick).
  - [ ] Agent does not proceed to deep scan until scope is clarified.
- **Guards tested:** Depth Control (Scan Protection).

### T50 — Manual Rename Rescue (Improv Mode)

- **Workflow:** `spec.md`
- **Synthetic State:**
  - `INDEX.md` references `core-api.md`.
  - `core-api.md` is missing from the disk.
  - `core-auth.md` exists on disk but is not registered.
  - Both files share 90% content similarity (same title and structure).
- **Action:** User runs command to sync specs or update the active plan.
- **Expected:**
  - [ ] Agent detects the missing spec and the unregistered spec.
  - [ ] Agent compares the content/title of the two specs.
  - [ ] Agent determines it is a **Manual Rename** (>80% similarity).
  - [ ] Agent successfully cascades the rename in `INDEX.md`, `PLAN.md`, and `TASKS.md` via the Spec Renaming Protocol without deleting tasks.
- **Guards tested:** Manual Rename Rescue (AOP), Spec Renaming Protocol.

### T51 — Analyze Smart Sync (AOP)

- **Workflow:** `analyze.md` (Re-Analysis Mode)
- **Synthetic State:**
  - `INDEX.md` references `auth.md`.
  - `auth.md` spec describes `src/auth/` (module deleted).
  - Directory `src/identity/` now exists (uncovered).
  - `auth.md` contains `# Title: Authentication System`.
- **Action:** User says "Re-analyze project"
- **Expected:**
  - [ ] Agent identifies `auth.md` as **Orphaned** and `src/identity/` as **Uncovered**.
  - [ ] Agent checks for title/content similarity (Smart Sync trigger).
  - [ ] Agent matches `Authentication System` title to `identity` module.
  - [ ] Re-Analysis report proposes `[RESCUE]` action instead of separate delete/create.
  - [ ] Gap Report status for `src/identity/` marked as `Manual Rename (Synced)`.
- **Guards tested:** Smart Sync (AOP) Rename detection, Gap Report RESCUE action.

### T52 — Spec Consistency Registry Integrity Missing File

- **Workflow:** `spec.md` (Consistency Check & Audit Report)
- **Synthetic State:**
  - `INDEX.md` references `data-model.md`.
  - `data-model.md` is deleted from disk (does not exist).
  - No unregistered spec exists (not a manual rename).
- **Action:** User says "Check specs"
- **Expected:**
  - [ ] Agent reads `INDEX.md` and identifies `data-model.md`.
  - [ ] Agent detects the file is completely missing from `.design/specifications/`.
  - [ ] Agent does NOT attempt to parse paths from the missing file (avoids crash).
  - [ ] Agent flags the **Registry Integrity** issue.
  - [ ] Consistency Report generated proposing to remove the orphaned entry from `INDEX.md` or restoring the file.
- **Guards tested:** Registry Integrity Guard, Missing File Exception Handling.

### T53 — Spec Deprecation Cascade with Implements Hierarchy

- **Workflow:** `spec.md` (Updating an Existing Specification)
- **Synthetic State:**
  - `auth-concept.md` (Stable L1), `auth-impl.md` (Stable L2, Implements: auth-concept.md)
- **Action:** User says "Deprecate auth-concept.md"
- **Expected:**
  - [ ] Status change: `auth-concept.md` → Deprecated
  - [ ] INDEX.md updated
  - [ ] **Deprecation Cascade**: `auth-impl.md` flagged as containing stale `Implements` link to `auth-concept.md`
  - [ ] Post-Update Review surfaces layer isolation logic (L2 has no valid L1 parent).
- **Guards tested:** Deprecation Cascade on Implements clause, Layer Integrity.

### T54 — Spec Rename History Immutability

- **Workflow:** `spec.md` (Updating an Existing Specification -> Spec Renaming Protocol)
- **Synthetic State:**
  - `RETROSPECTIVE.md` exists and contains mentions of `old-api.md`.
  - `.design/archives/tasks/phase-1.md` exists and contains mentions of `old-api.md`.
- **Action:** User renames `old-api.md` to `new-api.md`.
- **Expected:**
  - [ ] Status/Renaming applied: Agent updates active files (`INDEX.md`, `PLAN.md`, `TASKS.md`, active phase files, and `Related Specs`/`Implements`).
  - [ ] Agent explicitly excludes `RETROSPECTIVE.md` and `.design/archives/` from the search-and-replace sweep.
  - [ ] Mentions of `old-api.md` in historical logs are left completely intact.
- **Guards tested:** Historical Immutability Guard, Spec Renaming Protocol scoping.

### T55 — Spec Quarantine Cascade Enforcement (C12)

- **Workflow:** `spec.md` (Updating an Existing Specification)
- **Synthetic State:**
  - `auth-concept.md` (Stable L1)
  - `auth-impl.md` (Stable L2, Implements: auth-concept.md)
- **Action:** User says "Downgrade auth-concept.md to RFC"
- **Expected:**
  - [ ] Status change: `auth-concept.md` → RFC
  - [ ] Agent scans for dependencies and identifies `auth-impl.md` is a dependent L2 child.
  - [ ] **Quarantine Cascade**: Agent flags `auth-impl.md` during Post-Update Review.
  - [ ] **Status Drop Enforced**: Agent MUST drop status of `auth-impl.md` (L2) to RFC or Draft and update INDEX.md.
  - [ ] Agent alerts user: "L1 parent `auth-concept.md` is no longer Stable. `auth-impl.md` (L2) status dropped to maintain invariant §52."
- **Guards tested:** Quarantine Cascade (C12) surfacing, Layer Integrity.

### T56 — Task Quarantine Cascade (C12)

- **Workflow:** `task.md` (Updating Tasks & Plan)
- **Synthetic State:**
  - `auth-concept.md` (L1, status: RFC)
  - `auth-impl.md` (L2, status: Stable, Implements: auth-concept.md)
  - `PLAN.md` has `auth-impl.md` in Phase 1.
  - `TASKS.md` has task T-1A01 for `auth-impl.md` (Todo).
  - RULES.md v1.12.0 with C12.
- **Action:** Run `/magic.task update`
- **Expected:**
  - [ ] Agent identifies that `auth-concept.md` (L1) is not Stable.
  - [ ] **Quarantine Cascade (C12)**: `auth-impl.md` is moved to `## Backlog` in `PLAN.md`.
  - [ ] Task T-1A01 for `auth-impl.md` (Todo) → marked `Blocked [!]` with note: "Awaiting spec stabilization (C12 Quarantine)".
  - [ ] User is notified of the quarantine.
- **Guards tested:** Quarantine Cascade (C12) execution, Downgrade Policy.

### T57 — Parallel Mode Shared-Constraint Detection (Deep Scan)

- **Workflow:** `run.md` (Executing Tasks — Parallel Mode)
- **Synthetic State:**
  - Track A: T-1A01 "Update user module" (refs `user-module.md` §2).
  - Track B: T-1B01 "Add logging" (refs `logger.md` §4).
  - `user-module.md` §2 says "Modifies `src/lib/manager.js`".
  - `logger.md` §4 says "Updates logger middleware in `src/lib/manager.js`".
  - Task descriptions DO NOT mention `src/lib/manager.js`.
  - RULES.md §7 C3: Parallel mode.
- **Action:** Run `/magic.run`
- **Expected:**
  - [ ] Manager Agent reads both associated spec sections (§2 and §4).
  - [ ] **Shared-Constraint Detection**: Manager detects that BOTH tasks modify `src/lib/manager.js`.
  - [ ] Manager serializes the tasks (schedules T-1A01, then T-1B01 in sequence or same track).
  - [ ] Log entry recorded: "Serialization decision: T-1A01 and T-1B01 both modify `src/lib/manager.js`".
- **Guards tested:** Deep Shared-Constraint Detection (Spec Scan), Conflict Prevention.

### T58 — Run Rules-First Convention Enforcement

- **Workflow:** `run.md` (Executing Tasks)
- **Synthetic State:**
  - `TASKS.md` Phase 1 has 1 active task.
  - `RULES.md` §7 contains project-specific conventions (e.g., code quality guidelines, testing mandates).
- **Action:** Agent begins task execution.
- **Expected:**
  - [ ] Agent reads `RULES.md` before any code edit (Invariant 2: Rules First)
  - [ ] Agent applies all §7 conventions relevant to the task's technology stack
  - [ ] If `RULES.md` version > `TASKS.md` base version → Warn user of drift before executing
  - [ ] Task output adheres to conventions found in RULES.md (engine enforces reading, not specific convention content)
- **Guards tested:** Rules First invariant, convention sync guard.

### T59 — Engine Meta Automation Enforcement

- **Workflow:** `run.md`, `rule.md`, `simulate.md`, `spec.md` (Core Engine Update)
- **Synthetic State:**
  - Agent modifies `.magic/simulate.md` to add a new guideline.
  - `.magic/.version` is `1.4.11`.
  - `.magic/history/simulate.md` exists.
- **Action:** Agent performs the edit.
- **Expected:**
  - [ ] Agent identifies that a core engine file was modified.
  - [ ] Agent executes: `node .magic/scripts/executor.js update-engine-meta --workflow simulate`.
  - [ ] **Automated Verifications:**
    - [ ] `.magic/.version` bumped to `1.4.12`.
    - [ ] `.magic/history/simulate.md` contains a new row for `1.4.12`.
    - [ ] `.magic/.checksums` is recalculated.
  - [ ] Results documented in the task completion checklist.
- **Guards tested:** C1, C14, Engine Integrity Guard (via meta automation).

### T60 — Run Convention Sync Guard (Version Mismatch)

- **Workflow:** `run.md`
- **Synthetic State:**
  - `TASKS.md` header contains `Based on RULES: 1.4.6`.
  - `RULES.md` version is `1.4.7`.
  - Phase 1 has 3 Todo tasks.
- **Action:** Run `/magic.run`
- **Expected:**
  - [ ] Agent reads both versions during Pre-flight (Step 0).
  - [ ] **Mismatch Detected**: 1.4.6 vs 1.4.7.
  - [ ] Agent alerts user: "Project conventions have changed since these tasks were generated. Proceed or run `magic.task update` to synchronize?".
  - [ ] No execution begins until user chooses to proceed.
- **Guards tested:** Convention Sync Guard (Version Mismatch), Task-Rules parity.

### T61 — Init: Workspace Initialized

- **Workflow:** `init.md`
- **Synthetic State:**
  - `.design/` (missing).
- **Action:** Trigger any workflow (e.g. `spec.md`).
- **Expected:**
  - [ ] `check-prerequisites` fails (missing artifacts).
  - [ ] `init` workflow executes `init.js`.
  - [ ] `.design/workspace.json` is created with `default: root`.
  - [ ] `.design/RULES.md` and `INDEX.md` created.
- **Guards tested:** Core Artifact Initialization, Zero-Prompt baseline.

### T62 — Analyze: Depth Control (Threshold Enforcement)

- **Workflow:** `analyze.md`
- **Synthetic State:**
  - Project A: 40 files.
  - Project B: 200 files.
  - Project C: 600 files.
- **Action:** Run analysis (e.g. "Analyze project") on each.
- **Expected:**
  - [ ] **Project A**: Auto-scan (Step 1) starts without prompting.
  - [ ] **Project B**: Agent HALTs and asks: "Full or Focused scan?".
  - [ ] **Project C**: Agent recommends "Focused/Quick" and HALTs for choice.
- **Guards tested:** Depth Control (Safety) thresholds.

### T63 — Retro: Snapshot Archival (C8)

- **Workflow:** `retrospective.md` (Level 1 Snapshot)
- **Synthetic State:**
  - Workspace: `.design/api-v2/`
  - Current phase: Phase 3
  - File: `.design/api-v2/tasks/phase-3.md` exists.
  - `TASKS.md` has link to `tasks/phase-3.md`.
- **Action:** Phase 3 completes; `magic.run` triggers Retro L1.
- **Expected:**
  - [ ] `RETROSPECTIVE.md` (metadata) read or created.
  - [ ] Row appended to `RETROSPECTIVE.md` Snapshots table.
  - [ ] **Archival (C8)** executed: `phase-3.md` moved to `.design/api-v2/archives/tasks/phase-3.md`.
  - [ ] `TASKS.md` link updated to: `[Phase 3](archives/tasks/phase-3.md)`.
- **Guards tested:** C8 Archival, Workspace-relative pathing logic.

### T66 — Spec Registry-Filesystem Desync

- **Workflow:** `spec.md` (Updating an Existing Specification)
- **Synthetic State:**
  - `INDEX.md` lists `auth.md` (Stable).
  - `.design/specifications/auth.md` is **missing** from disk.
- **Action:** User says: "Update auth spec to include JWT."
- **Expected:**
  - [ ] `check-prerequisites` returns warning about missing file.
  - [ ] **Existence Guard** triggers.
  - [ ] **HALT** — Agent does not attempt to read `auth.md`.
  - [ ] Message: "Specification `auth.md` is registered in INDEX but missing from disk. Please restore or unregister before updating."
- **Guards tested:** Existence Guard (C1, Registry Drift).

### T67 — N-Level Circular Dependency

- **Workflow:** `task.md`
- **Synthetic State:**
  - `auth.md` (Stable, Related: api.md)
  - `api.md` (Stable, Related: database.md)
  - `database.md` (Stable, Related: auth.md)
- **Action:** Call `/magic.task` to generate a plan.
- **Expected:**
  - [ ] Dependency matrix construction (auth -> api -> database -> auth).
  - [ ] **Circular Guard** detects cycle at level 3.
  - [ ] **HALT** — No PLAN.md is written.
  - [ ] Agent visualizes the full cycle chain and asks user to break the link.
- **Guards tested:** N-Level Circular Dependency (C7).

### T68 — Simulation Cold Start Auto-Init

- **Workflow:** `simulate.md` (Step 0: Pre-flight)
- **Synthetic State:** Fresh repository, `.design/` (missing).
- **Action:** User runs `/magic.simulate`.
- **Expected:**
  - [ ] `check-prerequisites` returns `ok: false` (missing `.design/`).
  - [ ] No `ENGINE_INTEGRITY` or `checksums_mismatch` warnings (checksums are valid).
  - [ ] Auto-run `.magic/init.md` to create `.design/` structure.
  - [ ] After init completes, simulation resumes from Mode Selection.
- **Guards tested:** Auto-Init on missing `.design/`, resume after init.

### T69 — Quarantine Cascade Enforcement

- **Workflow:** `run.md` (Step 0: Pre-flight)
- **Synthetic State:**
  - `TASKS.md` Phase 1 has 1 Todo task for `api-impl.md`.
  - `INDEX.md` registers `api-impl.md` (Level 2) pointing to `api-core.md` (Level 1).
  - `api-core.md` status in `INDEX.md` = `RFC` (Not `Stable`).
- **Action:** User runs `/magic.run`.
- **Expected:**
  - [ ] `check-prerequisites` returns warning: "Rule 57 Violation: L2 spec 'api-impl.md' is ..., but its L1 parent 'api-core.md' is RFC (Must be Stable)."
  - [ ] **Quarantine Guard (C12)** in `run.md` detects violation for active task.
  - [ ] **HALT** — Execution does not begin.
  - [ ] Message: "Quarantine Triggered: Specification `api-impl.md` has a non-Stable parent. Please run `magic.task` to update your plan."
- **Guards tested:** Rule 57 Enforcement (C12), Runtime Quarantine Check.

### T70 — Scoped Analysis Guard (C15)

- **Workflow:** `analyze.md`
- **Synthetic State:**
  - `workspace.json`: `engine` workspace with `scope: [".magic/", ".agent/"]`.
  - Project has `src/`, `lib/`, `.magic/`, and `.agent/`.
- **Action:** User runs `/magic.analyze`.
- **Expected:**
  - [ ] `executor.js` exports `MAGIC_WORKSPACE_SCOPE=".magic/,.agent/"`.
  - [ ] **Scoping Rule (C15)**: Agent ignores `src/` and `lib/` during structure scan.
  - [ ] Proposal only includes modules found within the scoped paths.
- **Guards tested:** Scoped Scanning (C15), Multi-Workspace Isolation.

### T71 — Task Primary Intent Propagation (Cold Start Memory)

- **Workflow:** `task.md` -> `init.md` -> `analyze.md`
- **Synthetic State:**
  - `.design/` missing.
  - Projects has code.
- **Action:** User prompts: "Plan feature X" (starting magic.task).
- **Expected:**
  - [ ] `task.md` triggers `init.md`.
  - [ ] Agent suggests and runs `analyze.md`.
  - [ ] **Crucial**: After specs are approved, the agent automatically proposes a Plan/Task for "Feature X" using the newly generated specs.
  - [ ] Intent "Feature X" is NOT lost during the mapping/bootstrapping of existing code.
- **Guards tested:** Context Continuity, Intent Preservation.

### T72 — Engine Meta Auto-Heal (History Resilience)

- **Workflow:** `executor.js` (update-engine-meta)
- **Synthetic State:**
  - `.magic/spec.md` modified (checksum mismatch).
  - `.magic/history/spec.md` is MISSING from disk.
- **Action:** Run `node .magic/scripts/executor.js update-engine-meta --workflow spec`.
- **Expected:**
  - [ ] Executor detects missing history file.
  - [ ] **Action**: Executor creates a new `history/spec.md` with proper Markdown headers.
  - [ ] Version is bumped in `.version`.
  - [ ] Checksums regenerated in `.checksums`.
  - [ ] Report confirms restoration: "History file RESTORED (Auto-Heal)".
- **Guards tested:** Automated Restoration, Kernel Integrity (C1).

### T73 — Ghost Registry Repair Priority (Non-Destructive Boot)

- **Workflow:** `analyze.md` (Mode: Registry Repair)
- **Synthetic State:**
  - `.design/INDEX.md` is blank.
  - `.design/specifications/` has 3 files: `auth.md`, `db.md`, `api.md`.
- **Action:** User prompts: "Analyze project and suggest new specs".
- **Expected:**
  - [ ] Ghost Registry Guard (§52) triggers.
  - [ ] Agent explicitly ignores "suggest new specs" intent for now.
  - [ ] Agent proposes ONLY to map existing 3 files to `INDEX.md`.
  - [ ] Agent explains that new analysis is suspended until the registry is consistent.
  - [ ] Report: "Registry inconsistency found — repairing before analysis".
- **Guards tested:** Ghost Registry Guard, Intent Block (Safety).

### T74 — Cross-Workspace Name Collision (Source of Truth Guard)

- **Workflow:** `task.md` / `spec.md`
- **Synthetic State:**
  - `.design/workspace.json`: `default: engine`, secondary: `app`.
  - `.design/engine/specifications/core.md` (Version: 2.0.0, Stable).
  - `.design/app/specifications/core.md` (Version: 1.5.0, Stable) — stale copy.
  - Active workspace: `app`.
- **Action:** User runs `/magic.task` in `app`.
- **Expected:**
  - [ ] Agent identifies name collision across workspaces.
  - [ ] **Parity Guard** triggers: Version mismatch detected (2.0.0 vs 1.5.0).
  - [ ] **HALT**: Agent warns about "Source of Truth Drift".
  - [ ] Options: (A) Sync from engine, (B) Unique rename, (C) Force ignore.
- **Guards tested:** Cross-Workspace Parity Guard.

### T75 — Local Rule Constitutional Conflict (Hierarchy Guard)

- **Workflow:** `rule.md`
- **Synthetic State:**
  - Root `.design/RULES.md` §1 contains Core C1: "English only".
  - Active workspace: `.design/analytics/`.
- **Action:** User prompts in `analytics` workspace: "Add rule C8: Russian comments are allowed."
- **Expected:**
  - [ ] Agent identifies current workspace = `analytics`.
  - [ ] **Hierarchy Guard** scans ROOT RULES.md §1-6 (Constitution).
  - [ ] Agent detects that proposed C8 contradicts Root C1.
  - [ ] **HALT**: Agent refuses to add the rule.
  - [ ] Message: "Proposed local rule contradicts Global Constitution (§1 C1). Local conventions cannot override universal invariants."
- **Guards tested:** Cross-Workspace Constitutional Guard, Hierarchy Integrity.

### T76 — Quarantine Deadlock (Stabilization Exception)

- **Workflow:** `task.md` / `run.md` (C12 Enforcement)
- **Synthetic State:**
  - Parent `core-l1.md` (RFC).
  - Child `core-l2.md` (RFC, Quarantined by C12).
  - All tasks for `core-l2.md` are in Backlog/Blocked.
- **Action:** User prompts: "Pull tasks for core-l2.md into Phase 1 to fix implementation mismatches with Parent."
- **Expected:**
  - [ ] Agent identifies the intent is **Stabilization**, not new implementation.
  - [ ] **Stabilization Exception (C12.1)** triggers.
  - [ ] Agent allows pulling these tasks into Phase 1 despite non-stable parent.
  - [ ] Task notes explicitly state: "Exception C12.1 applied: Stabilization Mode".
  - [ ] **HALT** if the user tries to add NEW features to `core-l2.md` while it's in quarantine.
- **Guards tested:** C12.1 Stabilization Exception, Context-Aware Planning.

### T77 — Spec Merge Refactor (Section Re-mapping)

- **Workflow:** `spec.md` + `task.md` (Structural Refactor)
- **Synthetic State:**
  - `INDEX.md`: `auth.md` (Stable), `session.md` (Stable)
  - `TASKS.md`: `T-1A01` (auth.md §2), `T-2B01` (session.md §5)
- **Action:** User merges `auth.md` and `session.md` into `security.md`. §2 moves to §security.md §3.
- **Expected:**
  - [ ] **Structural Refactor detected**: Merge action recognized.
  - [ ] **Refactoring Guard**: Agent updates `T-1A01` in `TASKS.md` to point to `security.md §3`.
  - [ ] Agent updates `T-2B01` mapping if necessary.
  - [ ] `INDEX.md` synced: `auth.md`, `session.md` removed; `security.md` added.
  - [ ] `PLAN.md` synced with new spec name.
- **Guards tested:** Structural Refactor (Section Re-mapping), Refactoring Guard.
- **Outcome:** Agent identifies the merge, updates T-1A01 to point to `security.md §3`, and syncs registry.

### T78 — Simulation: Suite Integrity Failure

- **Workflow:** `simulate.md`
- **Synthetic State:**
  - `.magic/tests/suite.md` exists but lacks H3 headers for tests (uses only H2 or plain text).
- **Action:** Run `/magic.simulate test`
- **Expected:**
  - [ ] Agent reads `suite.md`.
  - [ ] **Structural Issue Detected**: "Suite integrity failure: missing H3 test headers".
  - [ ] Agent alerts user and proposes a fix for `suite.md` formatting.
  - [ ] Agent falls back to **Improv Mode** until fixed.
- **Guards tested:** Suite Integrity (Structural requirements), Fallback logic.

### T79 — Run: Changelog Precision (Filter Blocked)

- **Workflow:** `run.md`
- **Synthetic State:**
  - Phase 1: `T-101` (Done, Changes: "Added A"), `T-102` (Blocked, Changes: "Started B"), `T-103` (Done, Changes: "Added C").
- **Action:** Phase 1 completes. Agent triggers Changelog L1.
- **Expected:**
  - [ ] Agent reads Phase 1 tasks.
  - [ ] **Filtering applied**: Only `T-101` and `T-103` selected.
  - [ ] `CHANGELOG.md` updated with:
    - Added A
    - Added C
  - [ ] "Started B" is **NOT** present in the changelog.
- **Guards tested:** Changelog Filtering (Precision), Reporting Integrity.

### T80 — Rule: Rules Parity Sync Offer

- **Workflow:** `rule.md`
- **Synthetic State:**
  - `RULES.md` version 1.4.0.
  - `TASKS.md` header contains `Based on RULES: 1.4.0`.
- **Action:** User adds a new rule.
- **Expected:**
  - [ ] Agent proposes `RULES.md` update (version bump to 1.5.0).
  - [ ] Agent writes `RULES.md`.
  - [ ] **Rules Parity Check**: Agent detects `TASKS.md` is now stale.
  - [ ] Agent alerts user: "`TASKS.md` is based on rules v1.4.0 but project is now v1.5.0."
  - [ ] Agent offers to run `magic.task update` to synchronize the plan.
- **Guards tested:** Rules Parity (Stale check), Sync Offer.

### T81 — Spec T4 Rule with Missing Target File (HALT Persistence)

- **Workflow:** `spec.md` (T4 + Existence Guard)
- **Synthetic State:**
  - `INDEX.md` contains `auth.md` (Stable).
  - `auth.md` is missing from disk.
  - `RULES.md` v1.0.0.
- **Input:** `"Add MFA to auth.md and remember that all MFA must use TOTP."`
- **Expected:**
  - [ ] T4 detected ("remember that...").
  - [ ] Existence Guard fails for `auth.md` -> **HALT**.
  - [ ] Agent reports missing file.
  - [ ] **Crucial**: Agent acknowledges the T4 rule and confirms it is "queued" pending the resolution of the missing file issue.
  - [ ] Rule `C15 — MFA TOTP Standard` is NOT written to `RULES.md` until the target spec is restored or remapped.
- **Guards tested:** T4 persistence during HALT, Atomic Write Integrity.

### T82 — Init Migration: Existing Project Fallback

- **Workflow:** `init.md` + `run.md`
- **Synthetic State:**
  - Project root has `.design/` with existing specs/plans.
  - `.design/workspace.json` is missing.
- **Action:** User runs `/magic.run`
- **Expected:**
  - [ ] Agent falls back to root `.design/`.
  - [ ] Agent does not trigger an infinite loop of `init`.
  - [ ] `executor.js` identifies that `workspace.json` is missing and proceeds with root directory.
- **Guards tested:** Workspace Fallback (missing workspace.json), Init Loop Prevention.

### T83 — Micro-spec Promotion Guard

- **Workflow:** `spec.md` (Update flow)
- **Synthetic State:** Spec `bug-x.md` using `micro-spec.md` template, currently 45 lines.
- **Action:** User expands logic; new content makes it 75 lines.
- **Expected:**
  - [ ] Agent detects 50+ line threshold.
  - [ ] Agent proposes converting to `spec.md` template (Standard).
  - [ ] **HALT** if agent attempts to keep 75 lines in a legacy micro-template.
- **Guards tested:** Micro-spec Promotion Guard (C16), Template Threshold (50 lines).

### T84 — Init Migration: Index Preservation

- **Workflow:** `init.md` (Migration Mode)
- **Synthetic State:** Project with old `.design/INDEX.md` but no `workspace.json`.
- **Action:** User runs `/magic.init` or Auto-Init trigger.
- **Expected:**
  - [ ] Agent creates `workspace.json`.
  - [ ] **Guard**: Agent DOES NOT overwrite existing `INDEX.md` with default template.
  - [ ] Existing specifications remain registered.
- **Guards tested:** Non-Overwriting Invariant, Index Preservation (Migration).

### T85 — Engine Integrity Mandatory HALT

- **Workflow:** `check-prerequisites.js`
- **Synthetic State:**
  - `.magic/spec.md` is modified manually (hash mismatch).
- **Action:** Call any workflow.
- **Expected:**
  - [ ] `ok: false` in JSON output.
  - [ ] `warnings` contain "Engine Integrity".
  - [ ] Workflow (e.g., `run.md`) triggers HALT and does NOT begin execution.
- **Guards tested:** Engine Integrity Mandatory HALT (C1).

### T86 — Spec Consistency Audit: Version Drift Detection

- **Workflow:** `spec.md` (Consistency Check & Audit Report)
- **Synthetic State:**
  - `INDEX.md`: `documentation-system.md` v1.0.0 (Stable)
  - `documentation-system.md` file header: `Version: 1.1.0` — user manually bumped the version in the file after adding a new section, but forgot to update `INDEX.md`
  - Amendment rule was NOT applied (INDEX.md still shows v1.0.0, status still Stable)
- **Action:** User says "Verify specs" or "Check specs"
- **Expected:**
  - [ ] Agent reads all spec file headers and compares `Version:` against `INDEX.md` entries
  - [ ] `documentation-system.md` header version (1.1.0) ≠ INDEX.md version (1.0.0) → version mismatch detected
  - [ ] `documentation-system.md` flagged as `VERSION_DRIFT` in the Consistency Report
  - [ ] Agent reports: "Version header out of sync with registry — external edit without lifecycle protocol detected"
  - [ ] No automatic fix — issue surfaced for user resolution (update INDEX.md to 1.1.0 and apply amendment rule, or roll back file header)
  - [ ] Consistency Report includes `VERSION_DRIFT` category alongside existing checks
- **Guards tested:** Version Drift detection (RE-1), header-vs-registry mismatch, Consistency Check extension

### T87 — Run Spec Stability Spot-Check (RE-2)

- **Workflow:** `run.md` (Pre-flight — Spec Stability Guard)
- **Synthetic State:**
  - `TASKS.md` Phase 1: T-1A01 (Todo, maps to `auth-impl.md`)
  - `INDEX.md` at plan generation: `auth-impl.md` (Stable L2)
  - Between plan generation and run, user demotes `auth-impl.md` → RFC externally (edited INDEX.md directly)
  - `RULES.md §7` has C3: Parallel mode
  - No C12 violation (L1 parent `auth.md` is still Stable — this is NOT a parent-layer issue)
- **Action:** User runs `/magic.run`
- **Expected:**
  - [ ] Pre-flight: `check-prerequisites` passes (no engine mismatch)
  - [ ] **Spec Stability Spot-Check**: Agent reads `INDEX.md` for all Todo-task specs in current phase
  - [ ] `auth-impl.md` found with status `RFC` (not Stable)
  - [ ] **HALT** — execution does NOT begin
  - [ ] Message: "Spec `auth-impl.md` is no longer Stable (current: RFC). Run `magic.task update` to re-evaluate the plan."
  - [ ] C12 Quarantine guard does NOT fire (L1 parent is Stable — this is a different, complementary guard)
- **Guards tested:** Spec Stability Spot-Check (RE-2), direct spec demotion detection, guard independence from C12

### T88 — Version Drift Guard During Active Spec Update

- **Workflow:** `spec.md` (Updating an Existing Specification — Sync)
- **Synthetic State:**
  - `INDEX.md`: `api-core.md` v1.2.0 (Stable)
  - `api-core.md` file header: `Version: 1.3.0` — externally bumped by user; INDEX.md not updated
  - No active plan or tasks
- **Action:** User says "Update api-core.md to add a rate-limiting section"
- **Expected:**
  - [ ] Pre-flight Consistency Check runs: VERSION_DRIFT detected (`api-core.md` header 1.3.0 ≠ INDEX.md 1.2.0)
  - [ ] **Version Drift Guard fires → HALT** before any write to `api-core.md`
  - [ ] Agent reports: "Version drift on `api-core.md`: file header v1.3.0 ≠ registry v1.2.0. Resolve drift first: (a) sync INDEX.md and apply amendment rule, or (b) revert file header."
  - [ ] No changes written to `api-core.md` or `INDEX.md`
  - [ ] Execution resumes only after user resolves the drift
- **Guards tested:** Version Drift Guard (RE-3), update atomicity, HALT before write

### T89 — T4 Rule Queued on Version Drift HALT

- **Workflow:** `spec.md` (T4 + Version Drift Guard)
- **Synthetic State:**
  - `INDEX.md`: `api-core.md` v1.2.0 (Stable)
  - `api-core.md` file header: `Version: 1.3.0` (VERSION_DRIFT)
  - `RULES.md` v2.1.0, no rate-limiting rule
- **Input:** `"Update api-core.md to add a rate-limiting section, and remember that all API endpoints must include rate-limiting headers."`
- **Expected:**
  - [ ] T4 detected: "remember that all API endpoints must include rate-limiting headers"
  - [ ] Pre-flight Consistency Check: VERSION_DRIFT on `api-core.md` detected
  - [ ] **Version Drift Guard fires → HALT**
  - [ ] Agent acknowledges T4: "T4 rule detected — queued pending drift resolution. Rule will NOT be written to RULES.md until version drift on `api-core.md` is resolved."
  - [ ] No write to `RULES.md`, no write to `api-core.md`
  - [ ] After user resolves drift: T4 rule applied to `RULES.md`, spec update proceeds
- **Guards tested:** T4 queuing on VERSION_DRIFT HALT (RE-3 + RE-4), atomic write integrity, HALT persistence

### T90 — Intent Preservation Through Cold-Start Delegation Chain

- **Workflow:** `task.md` → `init.md` → `analyze.md` (Intent Preservation)
- **Synthetic State:**
  - `.design/` missing
  - Project has existing source code
- **Input:** User says "Plan the payment gateway feature" (starting `magic.task`)
- **Expected:**
  - [ ] `task.md` detects missing `.design/` → memos intent: "Plan the payment gateway feature"
  - [ ] Delegates to `init.md` → `.design/` created
  - [ ] Delegates to `analyze.md` → specs generated and approved
  - [ ] After delegation chain resolves: agent resumes explicitly: "Resuming: 'Plan the payment gateway feature'"
  - [ ] Agent generates tasks scoped to payment-related specs (intent NOT lost)
  - [ ] Intent "payment gateway feature" is visible in the final plan output
- **Guards tested:** Intent Preservation (RE-T71), cross-workflow context continuity

### T91 — Cross-Workspace Name Collision Parity Guard

- **Workflow:** `task.md` (Pre-flight — Cross-Workspace Parity)
- **Synthetic State:**
  - `workspace.json`: `default: engine`, secondary workspace: `app`
  - `.design/engine/specifications/core.md` Version: 2.0.0 (Stable)
  - `.design/app/specifications/core.md` Version: 1.5.0 (Stable) — stale copy
  - Active workspace: `app`
- **Action:** User runs `/magic.task` in `app` workspace
- **Expected:**
  - [ ] Pre-flight reads `workspace.json` → detects >1 workspace
  - [ ] Agent scans both workspaces for identically-named spec files
  - [ ] `core.md` found in both: `engine` v2.0.0, `app` v1.5.0 → version mismatch
  - [ ] **Cross-Workspace Parity Guard → HALT**
  - [ ] Report: "Source of Truth Drift: `core.md` exists in `engine` (v2.0.0) and `app` (v1.5.0)."
  - [ ] Options presented: (a) Sync from engine, (b) Rename unique per workspace, (c) Force ignore
  - [ ] No plan generated until user resolves
- **Guards tested:** Cross-Workspace Parity Guard (RE-T74), multi-workspace collision detection, HALT before planning

### T92 — Analyze Mode C with Empty INDEX.md (Precedence Guard)

- **Workflow:** `analyze.md` (Mode C — Mode Precedence)
- **Synthetic State:**
  - `.design/` initialized
  - `INDEX.md` exists but is empty (0 specs registered)
  - Project has source code
- **Action:** User runs `/magic.analyze`
- **Expected:**
  - [ ] Mode C fires (trigger matches `/magic.analyze`)
  - [ ] Mode A condition is also true (INDEX.md empty) — but Mode A does NOT auto-start
  - [ ] Mode C runs to completion: self-check, registry audit, coverage check, rule validation, report
  - [ ] Report delivered: "Registry empty — no specs registered. Coverage: 100% gap."
  - [ ] After report: agent offers "Would you like to run first-time analysis to generate spec proposals?"
  - [ ] Mode A starts only if user says yes
- **Guards tested:** Mode Precedence (RE-A1), Mode C completeness before Mode A offer

### T93 — Analyze Mode C Bypasses All Intermediate HALTs

- **Workflow:** `analyze.md` (Mode C — Audit Policy)
- **Synthetic State:**
  - `.magic/` checksum mismatch exists (`checksums_mismatch`)
  - `INDEX.md` has `api.md` registered but file is missing from disk (Existence Guard condition)
  - `auth.md` header `Version: 1.2.0`, INDEX.md entry `Version: 1.1.0` (VERSION_DRIFT)
  - L2 spec `api-impl.md` has non-Stable L1 parent (C12 Quarantine condition)
- **Action:** User runs `/magic.analyze`
- **Expected:**
  - [ ] `checksums_mismatch` detected — NOT halted, finding collected
  - [ ] `api.md` missing from disk — NOT halted (Existence Guard bypassed), finding collected
  - [ ] `auth.md` VERSION_DRIFT — NOT halted, finding collected
  - [ ] C12 Quarantine condition — NOT halted, finding collected
  - [ ] All 4 findings surfaced in the final consolidated report
  - [ ] Agent halts ONLY at report delivery (presents findings, awaits user action)
- **Guards tested:** Audit Policy HALT bypass (RE-A2), all 4 bypass categories

### T94 — Analyze Mode C Coverage Check with RESCUE AOP

- **Workflow:** `analyze.md` (Mode C — Coverage Check + RESCUE)
- **Synthetic State:**
  - `INDEX.md`: `auth.md` (Stable) — describes `src/auth/`
  - `src/auth/` deleted; `src/authentication/` exists (new uncovered directory)
  - `auth.md` title: "Authentication System"
  - Similarity between `auth.md` and `src/authentication/`: >80%
- **Action:** User runs `/magic.analyze`
- **Expected:**
  - [ ] Mode C Coverage Check runs within workspace scope
  - [ ] `src/auth/` → orphaned spec (`auth.md`)
  - [ ] `src/authentication/` → uncovered directory
  - [ ] RESCUE AOP: similarity >80% → classified as `RESCUE` (rename opportunity), NOT separate Gap + Orphan entries
  - [ ] Report: "RESCUE: `auth.md` likely renamed to `src/authentication/` — propose registry sync"
- **Guards tested:** RESCUE AOP in Mode C (RE-A3), rename detection, correct classification

### T95 — Analyze Mode C Scope Isolation (C15)

- **Workflow:** `analyze.md` (Mode C — Coverage Check Scope)
- **Synthetic State:**
  - Active workspace: `engine`; scope: `.magic/`, `docs/`
  - Project also has `src/`, `lib/` directories (out of scope)
  - `src/payments/` has no spec coverage
- **Action:** User runs `/magic.analyze`
- **Expected:**
  - [ ] Mode C Coverage Check reads workspace scope from `workspace.json`
  - [ ] Scan restricted to `.magic/` and `docs/` only
  - [ ] `src/payments/` NOT reported as a coverage gap (out of scope)
  - [ ] Only gaps within `.magic/` or `docs/` are reported
- **Guards tested:** C15 scope enforcement in Mode C Coverage Check (RE-A4)

### T96 — Analyze Mode C Checklist Completeness

- **Workflow:** `analyze.md` (Mode C — Task Completion)
- **Synthetic State:**
  - Clean engine workspace. Mode C runs successfully.
- **Action:** Mode C completes and agent presents checklist
- **Expected:**
  - [ ] Agent presents **Mode C: Ventilation** checklist (not Mode A/B checklist)
  - [ ] All 8 Mode C checklist items evaluated: self-check, registry audit, structural integrity (if workspace), coverage, rule validation, report delivery, advisory report, C14 not triggered
  - [ ] C14 not triggered (Mode C is read-only — C1 §7 confirmed)
  - [ ] No Mode A/B items (Depth Control, Stack/Arch, Dispatch) appear as pending items
- **Guards tested:** Mode C checklist separation (RE-A5), C14 exemption for read-only mode

### T97 — Spec Update Source of Truth Drift (Cross-Workspace Parity)

- **Workflow:** `spec.md` (§Updating → Sync — Cross-Workspace Parity)
- **Synthetic State:**
  - `workspace.json` registers two workspaces: `engine`, `app`.
  - `engine/auth.md` — Status: Stable, Version: 2.0.0.
  - `app/auth.md` — Status: Stable, Version: 1.5.0.
  - Active workspace: `app`.
- **Action:** "Update auth spec to add OAuth2 support"
- **Expected:**
  - [ ] Pre-flight detects `auth.md` exists in both `engine` (v2.0.0) and `app` (v1.5.0) — version mismatch
  - [ ] Agent **HALTs** before writing any updates to `app/auth.md`
  - [ ] Report: "Source of Truth Drift: `auth.md` exists in `engine` (v2.0.0) and `app` (v1.5.0)."
  - [ ] Three resolution options presented: (a) sync from canonical, (b) rename unique per workspace, (c) force ignore
  - [ ] No spec content written until user selects a resolution option
- **Guards tested:** RE-A6 (Cross-Workspace Parity in `spec.md` Pre-flight)

### T98 — RE-3 Drift Resolution Validation (Registry-Only Bump Without Review)

- **Workflow:** `spec.md` (§Updating → Sync — Version Drift Guard → Resolution Validation)
- **Synthetic State:**
  - `engine/auth.md` — file header Version: 1.2.0, INDEX.md entry: 1.1.0 (VERSION_DRIFT).
  - User resolves by bumping INDEX.md to 1.2.0 without reviewing the external change.
- **Action:** User says "resolved" after bumping INDEX.md only
- **Expected:**
  - [ ] Agent detects resolution was registry-sync-only (no amendment review)
  - [ ] Agent flags: "External change to `auth.md` between v1.1.0 and v1.2.0 was not reviewed."
  - [ ] Two options presented: (a) Yes — continue, (b) No — revert file header first
  - [ ] After user confirms (a), agent re-evaluates ALL Sync guards from the top before writing
  - [ ] No spec content written until re-evaluation completes
- **Guards tested:** RE-B1 (Resolution Validation sub-rule of Version Drift Guard)

### T99 — C12 Full Registry Scan (Dependents Not Currently Open)

- **Workflow:** `spec.md` (§Updating → Sync — C12 Quarantine)
- **Synthetic State:**
  - `engine/auth.md` — L1, Status: Stable → drops to RFC via amendment.
  - `engine/auth-jwt.md` — L2, `Implements: auth.md`, Status: Stable. Not open/loaded.
  - `engine/auth-oauth.md` — L2, `Implements: auth.md`, Status: Stable. Not open/loaded.
  - INDEX.md lists all three files.
- **Action:** Agent updates `auth.md` status to RFC
- **Expected:**
  - [ ] C12 scans INDEX.md (full registry), NOT just open files
  - [ ] Both `auth-jwt.md` and `auth-oauth.md` discovered as L2 dependents
  - [ ] Both dropped to RFC status
  - [ ] Report: "C12 Cascade: 2 dependents quarantined: [auth-jwt.md, auth-oauth.md]."
- **Guards tested:** RE-B2 (C12 full registry scan strategy)

### T100 — C12 Recursive Depth (L1→L2→L3 Chain)

- **Workflow:** `spec.md` (§Updating → Sync — C12 Quarantine recursive scan)
- **Synthetic State:**
  - `engine/auth.md` — L1, Status: Stable → drops to RFC.
  - `engine/auth-jwt.md` — L2, `Implements: auth.md`, Status: Stable.
  - `engine/auth-jwt-refresh.md` — L3, `Implements: auth-jwt.md`, Status: Stable.
- **Action:** Agent updates `auth.md` status to RFC
- **Expected:**
  - [ ] C12 scan finds `auth-jwt.md` (L2 of auth.md)
  - [ ] Recursive scan finds `auth-jwt-refresh.md` (L3, `Implements: auth-jwt.md`)
  - [ ] Both L2 and L3 dropped to RFC
  - [ ] Report: "C12 Cascade: 2 dependents quarantined: [auth-jwt.md, auth-jwt-refresh.md]."
  - [ ] No L3 silently missed due to fixed-depth scan
- **Guards tested:** RE-B2 (C12 recursive depth — L1→L2→L3)

### T101 — Analyze with Explicit Workspace Argument

- **Workflow:** `analyze.md` (§Workspace Resolution — Priority 1)
- **Synthetic State:**
  - `workspace.json` registers two workspaces: `engine`, `installers`. Default: `engine`.
- **Action:** `/magic.analyze installers`
- **Expected:**
  - [ ] Agent resolves workspace to `installers` (explicit arg overrides default)
  - [ ] Scan scope restricted to `installers/` paths as defined in `workspace.json`
  - [ ] No prompt to user; prints: "Active workspace: installers" or similar
  - [ ] `engine` workspace not scanned
- **Guards tested:** Workspace Resolution Priority 1 (explicit arg)

### T102 — Analyze Auto-Resolves Single Default Workspace

- **Workflow:** `analyze.md` (§Workspace Resolution — Priority 3, multiple + default)
- **Synthetic State:**
  - `workspace.json` registers two workspaces: `engine`, `installers`. Default: `engine`.
- **Action:** `/magic.analyze` (no argument)
- **Expected:**
  - [ ] Agent resolves workspace to `engine` (default from `workspace.json`)
  - [ ] No prompt to user; prints: "Active workspace: engine."
  - [ ] Analysis scoped to `engine` workspace paths
- **Guards tested:** Workspace Resolution Priority 3 (multiple workspaces + default)

### T103 — Analyze Asks When Multiple Workspaces and No Default

- **Workflow:** `analyze.md` (§Workspace Resolution — Priority 3, multiple + no default)
- **Synthetic State:**
  - `workspace.json` registers two workspaces: `engine`, `installers`. **No default field.**
- **Action:** `/magic.analyze` (no argument)
- **Expected:**
  - [ ] Agent detects multiple workspaces with no default and no explicit arg
  - [ ] Agent asks: "Which workspace to analyze? [engine, installers]"
  - [ ] Does NOT auto-pick either workspace
  - [ ] Does NOT start scanning before user responds
- **Guards tested:** Workspace Resolution Priority 3 (multiple workspaces, no default → ask)

### T104 — Analyze with Invalid MAGIC_WORKSPACE Env Var

- **Workflow:** `analyze.md` (§Workspace Resolution — Priority 2 validation)
- **Synthetic State:**
  - `workspace.json` registers two workspaces: `engine`, `installers`.
  - `MAGIC_WORKSPACE=frontend` (not in `workspace.json`).
- **Action:** `/magic.analyze` (no explicit arg)
- **Expected:**
  - [ ] Agent reads `MAGIC_WORKSPACE=frontend` (Priority 2)
  - [ ] Validates name against `workspace.json` — not found
  - [ ] **HALT**: "Unknown workspace 'frontend'. Available: [engine, installers]."
  - [ ] Does NOT silently fall through to Priority 3
- **Guards tested:** RE-C1 (MAGIC_WORKSPACE unknown-name validation)

### T105 — Explicit Arg Overrides MAGIC_WORKSPACE

- **Workflow:** `analyze.md` (§Workspace Resolution — Priority 1 override)
- **Synthetic State:**
  - `workspace.json` registers two workspaces: `engine`, `installers`. Default: `engine`.
  - `MAGIC_WORKSPACE=installers`.
- **Action:** `/magic.analyze engine`
- **Expected:**
  - [ ] Agent uses explicit arg `engine` (Priority 1 overrides Priority 2)
  - [ ] `MAGIC_WORKSPACE=installers` is ignored
  - [ ] Analysis scoped to `engine` workspace
  - [ ] No HALT or conflict warning
- **Guards tested:** RE-C4 (explicit arg overrides env var)

### T106 — Workspace Scope Auto-Applied from workspace.json

- **Workflow:** `analyze.md` (§Workspace Resolution — Scope Auto-Apply)
- **Synthetic State:**
  - `workspace.json` registers `installers` with `scope: ["installers/", "package.json"]`.
  - `MAGIC_WORKSPACE_SCOPE` not set.
- **Action:** `/magic.analyze installers`
- **Expected:**
  - [ ] Workspace resolved to `installers`
  - [ ] Scan boundary auto-set to `["installers/", "package.json"]` from `workspace.json` scope
  - [ ] Files outside `installers/` and `package.json` are NOT scanned
  - [ ] Agent does NOT require separate `MAGIC_WORKSPACE_SCOPE` env var to restrict scope
- **Guards tested:** RE-C2 (workspace scope auto-apply)

### T107 — Mode C Triggered with Workspace Arg via Natural Language

- **Workflow:** `analyze.md` (§Mode C trigger + workspace arg)
- **Synthetic State:**
  - `workspace.json` registers two workspaces: `engine`, `installers`. Default: `engine`.
- **Action:** "Ventilate installers"
- **Expected:**
  - [ ] Agent parses `installers` as the workspace argument from natural language
  - [ ] Mode C (Ventilation) triggered
  - [ ] Analysis scoped to `installers` workspace (not default `engine`)
  - [ ] Report covers `installers` scope only
- **Guards tested:** RE-C3 (Mode C trigger + workspace arg in natural language)

### T108 — Ghost Registry Critical HALT Barrier

- **Workflow:** `check-prerequisites.js`
- **Synthetic State:**
  - `cache-layer.md` registered in INDEX.md (Stable)
  - `cache-layer.md` is manually deleted from the `.design/specifications/` folder.
- **Action:** Any engine script/workflow triggered (e.g. `magic.task`)
- **Expected:**
  - [ ] `check-prerequisites.js` detects missing file while scanning `INDEX.md`.
  - [ ] `GHOST_REGISTRY` violation recorded.
  - [ ] **HALT** triggered: `ok: false` due to `GHOST_REGISTRY` failing `integrity_ok` check.
  - [ ] Workflow does not proceed to `view_file` or plan generation, preventing cascading hallucinations.
- **Guards tested:** Engine Integrity (Ghost Registry critical barrier)

### T110 — Mid-Run Spec Demotion Halts Track Before Done

- **Workflow:** `run.md` (§Execution Step 4 — Mid-Run Stability Check)
- **Synthetic State:**
  - Parallel mode active. Two tracks running:
    - Track A: executing `T-1A01` → target spec `auth.md` (L1, Stable at dispatch).
    - Track B: mid-execution, triggers `/magic.spec` amendment on `auth.md` → status drops to RFC.
  - Track A reaches Step 4 (Update) and attempts to commit `Done`.
- **Action:** Track A sets `T-1A01` → `Done`
- **Expected:**
  - [ ] Before committing `Done`, Track A re-reads `INDEX.md`
  - [ ] Detects `auth.md` is now RFC (demoted since dispatch)
  - [ ] **HALT**: "Spec `auth.md` demoted to RFC during execution of `T-1A01`. Task output suspended — run `magic.task update` to re-evaluate."
  - [ ] `T-1A01` NOT marked Done; left as In Progress
  - [ ] Manager notified of suspension
- **Guards tested:** RE-D1 (Mid-Run Stability Check before committing Done)

### T111 — Manager Re-Reads INDEX.md Before Next Assignment

- **Workflow:** `run.md` (§Execution Setup — Manager role)
- **Synthetic State:**
  - Parallel mode. Track A completes `T-1A01` (Done). Track B has demoted `auth.md` to RFC since Manager's last assignment.
  - Manager is about to assign next task `T-1A02` (also targets `auth.md`).
- **Action:** Manager proceeds to assign `T-1A02`
- **Expected:**
  - [ ] Manager re-reads `INDEX.md` before assigning `T-1A02`
  - [ ] Detects `auth.md` is RFC — not Stable
  - [ ] Does NOT assign `T-1A02`
  - [ ] Reports: "Spec `auth.md` is no longer Stable. Halting new assignments for dependent tasks."
  - [ ] Suggests: run `magic.task update` to re-evaluate the plan
- **Guards tested:** RE-D2 (Manager INDEX.md re-read cadence between assignments)

### T112 — Analyze Dispatch Cross-Workspace Name Collision on Create

- **Workflow:** `spec.md` (§Creating — Cross-Workspace Parity)
- **Synthetic State:**
  - `workspace.json`: `engine` (default), `app`.
  - `engine/auth.md` — Stable, v2.0.0.
  - `app/` INDEX.md: empty (0 specs).
- **Action:** `/magic.analyze app` → Mode A proposes `auth.md` for `app/` workspace → user approves → dispatch calls `spec.md` §Creating for `auth.md`
- **Expected:**
  - [ ] spec.md §Creating Pre-flight fires Cross-Workspace Parity check
  - [ ] Detects `auth.md` already exists in `engine` (v2.0.0)
  - [ ] **HALT** before creating `app/auth.md`
  - [ ] Report: "Name collision: `auth.md` already exists in `engine` (v2.0.0). Resolve before creating: (a) unique name, (b) promote existing as canonical, (c) force ignore."
  - [ ] `app/auth.md` NOT created until user resolves
- **Guards tested:** RE-E1 (Cross-Workspace Parity in spec.md §Creating)

### T113 — Mode B Logic Evolution Triggers Amendment Cascade

- **Workflow:** `analyze.md` (Mode B — Logic Evolution → dispatch)
- **Synthetic State:**
  - `app/auth.md` — L1, Stable, v1.0.0.
  - `app/auth-jwt.md` — L2, Stable, `Implements: auth.md`.
  - `app/src/auth/` — code has structurally drifted: 4 new sub-modules added (>30% threshold).
- **Action:** `/magic.analyze app` → Mode B detects Logic Evolution in `auth.md` → user approves Reality Sync
- **Expected:**
  - [ ] Logic Evolution detected: >30% new sub-modules in `src/auth/`
  - [ ] Reality Sync proposed: structured diff or "New Draft" of `auth.md`
  - [ ] User approves Reality Sync
  - [ ] Dispatch via `spec.md` Amendment Rule: `auth.md` status Stable → RFC
  - [ ] C12 cascade: `auth-jwt.md` (L2 dependent) status dropped to RFC
  - [ ] Report: "C12 Cascade: 1 dependent quarantined: [auth-jwt.md]."
  - [ ] No silent spec update — Amendment Rule and C12 both explicitly triggered
- **Guards tested:** RE-E2 (Logic Evolution amendment cascade + C12 in analyze.md Mode B)

### T114 — Analyze Mode A Pre-flight Step 0 Enforcement

- **Workflow:** `analyze.md` (Mode A — Step 0)
- **Synthetic State:**
  - `.design/` initialized, `INDEX.md` empty (0 specs)
  - Project has 300 source files
- **Action:** `/magic.analyze`
- **Expected:**
  - [ ] Mode C runs first (Mode Precedence), then user accepts Mode A
  - [ ] Mode A Step 0 fires: `check-prerequisites` called
  - [ ] Depth Control applied: 300 files → agent asks "Full or Focused?"
  - [ ] Agent does NOT start "Build full project map" until user responds
- **Guards tested:** Mode A Step 0 Pre-flight, Depth Control enforcement in operational steps

### T115 — Analyze Mode B Pre-flight Step 0 Enforcement

- **Workflow:** `analyze.md` (Mode B — Step 0)
- **Synthetic State:**
  - `INDEX.md` has 5 active specs
  - Project has 800 source files
- **Action:** "Re-analyze project"
- **Expected:**
  - [ ] Mode B Step 0 fires: `check-prerequisites` called
  - [ ] Depth Control applied: 800 files → agent recommends Focused/Quick, HALTs for choice
  - [ ] Agent does NOT start reading specs (Step 1) until user responds
- **Guards tested:** Mode B Step 0 Pre-flight, Depth Control enforcement for large projects

### T116 — Analyze Direct Trigger Auto-Init

- **Workflow:** `analyze.md` (Auto-Init — Invariant 2)
- **Synthetic State:**
  - `.design/` does NOT exist
  - Project has source code
- **Action:** `/magic.analyze` (direct trigger, NOT via `spec.md` delegation)
- **Expected:**
  - [ ] `analyze.md` Invariant 2 fires: `.design/` missing detected
  - [ ] Auto-trigger `.magic/init.md` before any scanning
  - [ ] `.design/` created with all 5 artifacts
  - [ ] Analysis resumes after init completes
- **Guards tested:** Auto-Init (Invariant 2) on direct analyze trigger

### T117 — Spec Delta-Editing Enforcement (>200 Lines)

- **Workflow:** `spec.md` (Updating an Existing Specification)
- **Synthetic State:**
  - `auth.md` (Stable, 250 lines)
  - User requests adding a new section
- **Action:** Agent updates `auth.md`
- **Expected:**
  - [ ] Pre-flight detects >200 lines → delta-editing mode activated (Invariant 9)
  - [ ] Agent uses search-replace operations instead of full file rewrite
  - [ ] Changed sections marked with `[ADDED]`, `[MODIFIED]`, or `[REMOVED]`
  - [ ] No content corruption from full-file replacement on large spec
- **Guards tested:** Delta-Editing enforcement (Invariant 9) in operational step

### T118 — Spec Ventilation Routing (No Phantom C21)

- **Workflow:** `spec.md` (Ventilation invariant)
- **Synthetic State:**
  - `.design/` initialized, INDEX.md has 5 specs
  - User says "Ventilate" or "Check specs deeply"
- **Action:** Agent processes ventilation intent
- **Expected:**
  - [ ] Agent routes to `analyze.md` Mode C (not a phantom C21 convention)
  - [ ] `analyze.md` is read and its workflow followed
  - [ ] No reference to undefined convention ID in agent output
- **Guards tested:** Ventilation routing without phantom convention reference

### T119 — Analyze Argument Routing: Workspace vs Focus Disambiguation

- **Workflow:** `analyze.md` (§Argument Routing)
- **Synthetic State:**
  - `workspace.json` registers: `engine`, `installers`.
- **Test A — Unquoted workspace name:**
  - **Action:** `/magic.analyze engine`
  - **Expected:**
    - [ ] Argument matches workspace name → Workspace Analysis mode
    - [ ] Mode C (with Structural Integrity) → A/B scoped to `engine`
- **Test B — Quoted workspace name (force focus):**
  - **Action:** `/magic.analyze "engine"`
  - **Expected:**
    - [ ] Argument is quoted → treated as focus text, NOT workspace
    - [ ] Mode D triggered: focus directive = "engine"
    - [ ] Agent searches for project areas matching keyword "engine"
- **Test C — Workspace + focus:**
  - **Action:** `/magic.analyze installers "check tests"`
  - **Expected:**
    - [ ] First token `installers` matches workspace → workspace resolved
    - [ ] Remaining `"check tests"` → focus directive
    - [ ] Mode D scoped to `installers` workspace
- **Guards tested:** Argument Routing disambiguation, quote-wrapping override

### T120 — Analyze Mode D: Focused Analysis on Specific Area

- **Workflow:** `analyze.md` (Mode D — Focused Analysis)
- **Synthetic State:**
  - `workspace.json`: `app` workspace, scope: `src/`
  - `INDEX.md` has 3 specs: `api.md` (covers `src/api/`), `auth.md` (covers `src/auth/`), `ui.md` (covers `src/components/`)
  - `src/api/` has 5 files, `src/auth/` has 3 files, `src/components/` has 20 files
  - `src/utils/` exists (no spec, 8 files)
- **Action:** `/magic.analyze app "check API coverage"`
- **Expected:**
  - [ ] Focus directive parsed: intent = API coverage check
  - [ ] Targeted scan: only `src/api/` and related API areas examined (not full project)
  - [ ] Focused Gap Report: `src/api/` → Covered by `api.md`
  - [ ] `src/utils/` NOT reported (out of focus scope)
  - [ ] Advisory Report included, scoped to API area
  - [ ] Depth Control exempt (targeted scan)
- **Guards tested:** Mode D focus parsing, targeted scan scope, Advisory inclusion

### T121 — Analyze Mode D: Focus Matches Nothing

- **Workflow:** `analyze.md` (Mode D — HALT on no match)
- **Synthetic State:**
  - `workspace.json`: `engine` workspace
  - Project has `src/core/`, `src/scripts/`, `docs/`
- **Action:** `/magic.analyze "blockchain integration"`
- **Expected:**
  - [ ] Focus directive parsed: intent = blockchain integration
  - [ ] Targeted scan: no folders, spec titles, or modules match "blockchain"
  - [ ] **HALT**: "Could not map focus 'blockchain integration' to any project area. Try narrowing with a workspace: `/magic.analyze {workspace} \"blockchain integration\"`, or rephrase the focus."
  - [ ] No scan started, no report generated
- **Guards tested:** Mode D HALT on empty match, improved HALT message

### T122 — Analyze Mode C: Structural Integrity Violations

- **Workflow:** `analyze.md` (Mode C — Structural Integrity step)
- **Synthetic State:**
  - `workspace.json` registers `api` workspace with scope `src/api/`, folder `.design/api/`
  - `.design/api/` exists but:
    - `INDEX.md` is missing
    - `specifications/` contains `My Spec.md` (not kebab-case)
    - `specifications/orphan-spec.md` exists but is NOT listed in workspace INDEX
  - `workspace.json` scope entry `src/legacy/` does NOT exist on disk
- **Action:** `/magic.analyze api`
- **Expected:**
  - [ ] Structural Integrity fires (workspace specified)
  - [ ] STRUCTURE violation: `INDEX.md` missing (required)
  - [ ] STRUCTURE violation: `My Spec.md` — not kebab-case
  - [ ] STRUCTURE violation: `orphan-spec.md` — file exists but no INDEX entry (cross-reference mismatch)
  - [ ] STRUCTURE violation: scope path `src/legacy/` does not exist on disk
  - [ ] All violations reported under `STRUCTURE` category (separate from Drift/Gap/Orphan)
  - [ ] Mode C continues to subsequent steps (coverage, rules) after structural report
- **Guards tested:** Structural Integrity all 6 sub-checks, STRUCTURE category separation

### T123 — Analyze Advisory Report Generation Across Modes

- **Workflow:** `analyze.md` (§Advisory Report — all modes)
- **Synthetic State:**
  - `workspace.json`: `app` workspace
  - `INDEX.md` has 2 specs:
    - `core.md` — L1 Stable, 350 lines (oversized), no L2 children
    - `utils.md` — L2 Stable, no L1 parent
  - `src/tests/` directory: 15 files, no corresponding spec
  - `app/RULES.md` §7 repeats 2 conventions already in global `RULES.md` §6
- **Test A — Mode A generates Advisory:**
  - **Action:** INDEX.md empty → Mode A runs → Advisory step fires
  - **Expected:**
    - [ ] Advisory Report appended to Mode A output
- **Test B — Mode B generates Advisory:**
  - **Action:** INDEX.md has specs → Mode B runs → Advisory step fires
  - **Expected:**
    - [ ] Spec Quality: `core.md` flagged as oversized (>300 lines), split suggested
    - [ ] Spec Quality: `core.md` flagged as bare L1 (no L2 children)
    - [ ] Spec Quality: `utils.md` flagged as orphan L2 (no parent L1)
    - [ ] Coverage Strategy: `src/tests/` flagged (15 files, no spec) → suggest `test-suite.md`
    - [ ] Structural Improvements: 2 rule duplicates flagged → suggest promoting to global
    - [ ] Each finding has concrete Action Proposal (`→ /magic.spec ...` or `→ /magic.rule ...`)
- **Test C — Mode C generates Advisory:**
  - **Action:** `/magic.analyze app` → Mode C completes → Advisory step fires
  - **Expected:**
    - [ ] Advisory Report appended after Mode C report (step 9)
    - [ ] Same findings as Test B (spec quality + coverage + structural)
- **Guards tested:** Advisory generation in all modes (not just Mode D), Action Proposals format

### T124 — Analyze Mode D: Depth Control Fallback on Wide Focus

- **Workflow:** `analyze.md` (Mode D — Depth Control exemption + fallback)
- **Synthetic State:**
  - Large project: 800 source files
  - No workspace specified
- **Test A — Narrow focus:**
  - **Action:** `/magic.analyze "authorization"`
  - **Expected:**
    - [ ] Focus matches `src/auth/` (12 files) → Depth Control exempt
    - [ ] Targeted scan proceeds without prompting
- **Test B — Wide focus resolving to >500 files:**
  - **Action:** `/magic.analyze "all components"`
  - **Expected:**
    - [ ] Focus matches `src/` (600+ files)
    - [ ] Depth Control fallback triggers: agent recommends Focused/Quick, HALTs for choice
    - [ ] Agent does NOT auto-scan 600+ files
- **Guards tested:** Mode D Depth Control exemption for narrow focus, fallback for wide focus (>500 files)

### T125 — Analyze Mode C: Scope Blind-Spot Detection

- **Workflow:** `analyze.md` (Mode C — Scope Blind-Spot Check)
- **Synthetic State:**
  - `workspace.json` registers: `api` (scope: `packages/api/`), `web` (scope: `packages/web/`)
  - Project also has `packages/shared/`, `infra/`, `scripts/` at top level
  - None of these extra directories are in any workspace scope
- **Action:** `/magic.analyze api`
- **Expected:**
  - [ ] Mode C step 5 fires: union of all workspace scopes = `packages/api/` + `packages/web/`
  - [ ] `packages/shared/`, `infra/`, `scripts/` detected as not in any scope
  - [ ] Report includes `UNSCOPED` warnings for each: "Directory 'packages/shared/' is not in any workspace scope — invisible to scoped analysis."
  - [ ] Warnings are non-halting (informational, included in consolidated report)
- **Guards tested:** Scope Blind-Spot Check, UNSCOPED category

### T126 — Analyze Registry Audit: Case Mismatch on Case-Insensitive FS

- **Workflow:** `analyze.md` (Mode C — Registry Audit exact match)
- **Synthetic State:**
  - OS: Windows (case-insensitive filesystem)
  - `INDEX.md` lists `api-routes.md`
  - Disk file is `specifications/API-Routes.md`
  - File is accessible via both names on Windows
- **Action:** `/magic.analyze api`
- **Expected:**
  - [ ] Registry Audit uses exact string match (not OS file-exists)
  - [ ] `api-routes.md` (INDEX) ≠ `API-Routes.md` (disk) → registry violation detected
  - [ ] Structural Integrity also flags `API-Routes.md` as non-kebab-case
  - [ ] Report includes both violations (registry mismatch + naming convention)
  - [ ] Agent does NOT report "file not found" — it recognizes the case mismatch
- **Guards tested:** Exact string match in Registry Audit, case-insensitive FS edge case

### T127 — Analyze Mode D: Project-Wide Focus Bypasses C15

- **Workflow:** `analyze.md` (Mode D — C15 exception)
- **Synthetic State:**
  - `workspace.json`: `api` (scope: `packages/api/`), `web` (scope: `packages/web/`)
  - `packages/shared/utils.js` exists (not in any workspace scope)
  - No workspace argument provided
- **Test A — Focus without workspace:**
  - **Action:** `/magic.analyze "utils"`
  - **Expected:**
    - [ ] Mode D triggered, no workspace → project-wide scan
    - [ ] C15 scope NOT enforced (focus is the boundary)
    - [ ] `packages/shared/utils.js` found and included in Focused Gap Report
    - [ ] Directories outside all scopes are reachable
- **Test B — Focus with workspace:**
  - **Action:** `/magic.analyze api "utils"`
  - **Expected:**
    - [ ] Mode D triggered, workspace `api` → C15 applied (scope: `packages/api/`)
    - [ ] `packages/shared/utils.js` NOT found (out of `api` scope)
    - [ ] Only `packages/api/` searched for "utils" matches
- **Guards tested:** Mode D C15 exception (project-wide), C15 enforcement (workspace-scoped)

### T128 — Simulate C14 Enforcement Gate Blocks Report

- **Workflow:** `simulate.md` (§Reporting & Fixes — C14 Enforcement Gate)
- **Synthetic State:**
  - Agent ran `/magic.simulate spec` and found 2 ROUGH EDGEs
  - Agent applied surgical patches to `.magic/spec.md`
  - Agent is about to report results
- **Action:** Agent reaches Reporting step
- **Expected:**
  - [ ] C14 Enforcement Gate fires: "were any `.magic/` files modified during this `/magic.simulate` invocation?"
  - [ ] Answer: yes (`spec.md` patched) → `update-engine-meta --workflow simulate` runs
  - [ ] `.version` bumped, `.checksums` regenerated
  - [ ] Only AFTER checksums match does the agent present results
  - [ ] If agent skips Gate and reports first → **FAIL**
- **Guards tested:** C14 Enforcement Gate blocking semantics

### T129 — Simulate Succession Max 2-Round Guard

- **Workflow:** `simulate.md` (§Succession — max iterations)
- **Synthetic State:**
  - Round 1: `/magic.simulate test` finds 1 FAIL → agent patches → C14 Gate → Succession
  - Round 2: `/magic.simulate test` finds 1 new FAIL (introduced by Round 1 fix) → agent patches → C14 Gate → Succession
  - Round 3 would start
- **Action:** Agent reaches 3rd Succession attempt
- **Expected:**
  - [ ] Agent detects round >2
  - [ ] Agent does NOT start a 3rd fix cycle
  - [ ] Agent reports: "Max Succession rounds (2) reached. Remaining issues: [list]."
  - [ ] Simulation completes with open issues documented
- **Guards tested:** Succession max 2-round guard, infinite loop prevention

### T130 — Simulate File-Path Argument Routing

- **Workflow:** `simulate.md` (§Mode Selection — file-path support)
- **Synthetic State:**
  - All engine files present and valid
- **Test A — Workflow name:**
  - **Action:** `/magic.simulate spec`
  - **Expected:**
    - [ ] Direct mode: cognitive walkthrough of `spec.md`
- **Test B — File path:**
  - **Action:** `/magic.simulate @/path/to/magic.analyze.md`
  - **Expected:**
    - [ ] File path parsed: workflow name extracted as `analyze`
    - [ ] Direct mode: cognitive walkthrough of `analyze.md`
    - [ ] Same behavior as `/magic.simulate analyze`
- **Guards tested:** File-path argument parsing, equivalence with workflow-name argument

### T131 — Checklist Consolidation Strategic/Tactical Split

- **Workflow:** `task.md` + `run.md`
- **Synthetic State:**
  - 2 Stable specs: `auth.md`, `api.md`
  - RULES.md v1.3.0 (contains C10 Checklist Consolidation)
  - templates/plan.md and templates/tasks.md updated
- **Action 1: Generate tasks (`task.md`)**
- **Expected 1:**
  - [ ] `PLAN.md` created: contains high-level entries for `auth.md` and `api.md` with single `[ ]` checkboxes. **No nested atomic tasks.**
  - [ ] `TASKS.md` created: contains **Phase Checklist** with atomic items prefixed with `[T-XXXX]` (e.g., `[ ] [T-1A01] Implement auth login`).
  - [ ] `TASKS.md` details section contains full task blocks.
- **Action 2: Execute task T-1A01 (`run.md`)**
- **Expected 2:**
  - [ ] T-1A01 implementation complete.
  - [ ] **`TASKS.md` Phase Checklist** updated: `[ ]` → `[x]` for T-1A01.
  - [ ] **`PLAN.md` remains unchanged** (since only one task of two for `auth.md` is done).
- **Action 3: Execute final task for auth.md**
- **Expected 3:**
  - [ ] All tasks for `auth.md` marked `[x]` in `TASKS.md`.
  - [ ] Agent recognizes `auth.md` completion.
  - [ ] **`PLAN.md` updated**: `[ ]` → `[x]` for `auth.md` specification.
- **Guards tested:** C10 Strategic/Tactical split, status sync isolation (atomic in TASKS, spec-level in PLAN).

### T132 — Run File-Header Parity Catches Manual Demotion

- **Workflow:** `run.md`
- **Synthetic State:**
  - `installer-architecture.md` (L1): file header `Status: Draft`, `Version: 2.0.0`
  - `INDEX.md` entry for `installer-architecture.md`: `Status: Stable`, `Version: 1.0.0`
  - Active phase-1 tasks reference `installer-node.md` (L2, Implements: installer-architecture.md)
- **Action:** `/magic.run` triggered to execute phase-1 tasks
- **Expected:**
  - [ ] Pre-flight File-Header Parity detects STATUS_DRIFT on `installer-architecture.md` (file=Draft ≠ INDEX=Stable)
  - [ ] Pre-flight File-Header Parity detects VERSION_DRIFT on `installer-architecture.md` (file=2.0.0 ≠ INDEX=1.0.0)
  - [ ] **HALT** before any task execution with drift report
  - [ ] C12 cascade is NOT triggered prematurely (drift must be resolved first)
  - [ ] User directed to resolve via `magic.spec` or `magic.analyze`
- **Guards tested:** File-Header Parity (run.md), STATUS_DRIFT, VERSION_DRIFT, C12 pre-condition ordering

### T133 — Task Pre-flight File-Header Parity Scan

- **Workflow:** `task.md`
- **Synthetic State:**
  - `engine/INDEX.md` lists `engine-core.md` as Stable v1.1.0
  - Actual file `engine-core.md` header: `Status: RFC`, `Version: 1.2.0` (manual edit)
  - `engine-automation.md` (L2, Implements: engine-core.md) listed as Stable
- **Action:** `/magic.task` triggered to generate plan
- **Expected:**
  - [ ] Pre-flight File-Header Parity detects STATUS_DRIFT on `engine-core.md` (file=RFC ≠ INDEX=Stable)
  - [ ] Pre-flight File-Header Parity detects VERSION_DRIFT on `engine-core.md` (file=1.2.0 ≠ INDEX=1.1.0)
  - [ ] **HALT** before plan generation
  - [ ] `engine-automation.md` is NOT moved to Backlog yet (drift must be resolved before C12 evaluates)
- **Guards tested:** File-Header Parity (task.md), STATUS_DRIFT blocks C6/C12 evaluation

### T134 — Spec Version Drift Guard Scans Dependency Chain

- **Workflow:** `spec.md`
- **Synthetic State:**
  - Target: `installer-node.md` (L2, Implements: installer-architecture.md)
  - `installer-node.md` header matches INDEX.md (no drift)
  - `installer-architecture.md` (L1 parent): file header `Version: 2.0.0`, INDEX.md says `Version: 1.0.0`
- **Action:** `/magic.spec` update `installer-node.md` with "add plugin hooks"
- **Expected:**
  - [ ] Version Drift Guard scans dependency chain: `installer-node.md` → `installer-architecture.md`
  - [ ] Detects VERSION_DRIFT on parent `installer-architecture.md` (file=2.0.0 ≠ INDEX=1.0.0)
  - [ ] **HALT** before writing updates to `installer-node.md`
  - [ ] Report names the drifted dependency (not just the target)
  - [ ] User directed to resolve parent drift first
- **Guards tested:** Version Drift Guard (dependency chain scan), Related Specifications traversal

### T135 — Simulate Pre-flight Blocks on Engine Integrity Failure

- **Workflow:** `simulate.md` (§0 Pre-flight)
- **Synthetic State:**
  - `.magic/.checksums` has been manually altered (hash mismatch)
  - `check-prerequisites --json` returns `checksums_mismatch: true`
- **Action:** `/magic.simulate test` triggered
- **Expected:**
  - [ ] Pre-flight Step 0 runs `check-prerequisites --json`
  - [ ] Agent detects `checksums_mismatch` in output
  - [ ] **HALT** with report: "Engine integrity failure — resolve before simulating."
  - [ ] Agent does NOT fall through to Mode Selection or execute any test scenarios
  - [ ] No suite.md tests are evaluated
- **Guards tested:** Pre-flight engine integrity gate (Step 0), HALT-before-mode-selection enforcement

### T136 — Improv Mode Crisis Template Structural Validation

- **Workflow:** `simulate.md` (§1a Crisis Template)
- **Synthetic State:**
  - `workspace.json` has 2 workspaces: `engine`, `installers`
  - All engine files valid
- **Action:** `/magic.simulate` (no args — Improv mode)
- **Expected:**
  - [ ] Agent synthesizes a crisis with a named scenario (CR-6)
  - [ ] Crisis header block presented before walkthrough with all CR-1 through CR-6 fields
  - [ ] CR-1: ≥2 workflows affected (listed explicitly)
  - [ ] CR-2: Full Spec→Task→Run chain traced (no link skipped)
  - [ ] CR-3: ≥2 workspaces involved (since `workspace.json` has >1)
  - [ ] CR-4: ≥3 distinct C{N} guards targeted (listed by ID)
  - [ ] CR-5: ≥1 out-of-band mutation described
  - [ ] If any CR requirement is not met and not documented as skipped → **FAIL**
- **Guards tested:** Crisis Template completeness, CR-1 through CR-6 enforcement

### T137 — Simulate Guard Resilience Reports Mechanical vs Instructional

- **Workflow:** `simulate.md` (§3 Cognitive Coverage Report — Guard Resilience)
- **Synthetic State:**
  - Target: `run.md`
  - Guards applicable: C12 (mechanical — INDEX.md check), C7 (instructional — no HALT keyword), C14 (mechanical — checksums), C3 (instructional — RULES.md §7 with HALT)
- **Action:** Agent evaluates Guard Resilience metric for `run.md`
- **Expected:**
  - [ ] Each guard classified as **Mechanical** or **Instructional** before testing
  - [ ] Mechanical guards tested against script output behavior (PASS/FAIL)
  - [ ] Instructional guards tested for explicit HALT keyword presence (PASS/PARTIAL)
  - [ ] C7 scored as PARTIAL (instruction exists, no HALT keyword, relies on LLM compliance)
  - [ ] C3 scored as PASS (explicit HALT in run.md: "If missing → **HALT**")
  - [ ] Final report uses format: `"Mechanical: X/Y, Instructional: A/B (C partial)"`
  - [ ] Single combined score calculated but breakdown visible
- **Guards tested:** Guard Resilience metric decomposition, Mechanical vs Instructional classification

### T138 — Simulate Context Bleed Warning in Succession Report

- **Workflow:** `simulate.md` (§3 Succession — Context Bleed Warning)
- **Synthetic State:**
  - Agent ran `/magic.simulate spec`, found 1 ROUGH EDGE, applied fix
  - C14 gate passed
  - Succession round 1: 0 regressions
- **Action:** Agent produces final simulation report
- **Expected:**
  - [ ] Report includes context bleed warning: `"⚠ Succession ran in-context. For unbiased verification, run /magic.simulate test in a fresh session."`
  - [ ] Warning appears in final report text (not buried in checklist)
  - [ ] If warning is missing → **FAIL**
- **Guards tested:** Context Bleed Warning enforcement, wrapper-implementation sync

### T139 — Suite Integrity Timing: Test Mode Validates Before Execution

- **Workflow:** `simulate.md` (§2 Suite Integrity — timing rule)
- **Synthetic State:**
  - `.magic/tests/suite.md` exists but T15 has a malformed header: `### T15: Missing Dash` (colon instead of dash)
  - suite.md has 20 valid tests + 1 malformed
- **Action:** `/magic.simulate test` triggered
- **Expected:**
  - [ ] Suite Integrity check runs **before** scenario execution (timing: `test` mode)
  - [ ] Malformed T15 detected: header uses `:` instead of `—` (dash)
  - [ ] Agent reports structural violation before PASS/FAIL table
  - [ ] Agent either skips T15 with a note or halts for repair
  - [ ] Remaining 20 valid tests proceed normally
- **Guards tested:** Suite Integrity timing (pre-execution in test mode), structural format enforcement

### T140 — Context Resolution Consistency Across Workflows

- **Workflow:** All workflows (`spec.md`, `task.md`, `run.md`, `analyze.md`, `init.md`, `rule.md`, `simulate.md`)
- **Synthetic State:**
  - `workspace.json` has 2 workspaces: `engine` (default), `installers`
  - `MAGIC_WORKSPACE` env var is set to `installers`
  - User runs `/magic.spec` (no explicit workspace arg)
- **Expected:**
  - [ ] Agent resolves workspace using priority chain: explicit arg (none) > `MAGIC_WORKSPACE` (`installers`) → uses `installers`
  - [ ] Same resolution logic produces same result in `task.md`, `run.md`, `rule.md`, `simulate.md`, `init.md`
  - [ ] `analyze.md` full Workspace Resolution table produces identical result for same inputs
  - [ ] No workflow falls back to `workspace.json` default when `MAGIC_WORKSPACE` is set
- **Guards tested:** Context Resolution parity across all workflows, priority chain consistency

### T141 — Trust Mode Terminology Consistency

- **Workflow:** `spec.md` (Status Lifecycle, Dispatching, Actionable Outcome)
- **Synthetic State:**
  - Input: "Add JWT auth to the API"
  - No RULES.md conflicts, no circular dependencies, no VERSION_DRIFT
  - `auth.md` exists (Stable)
- **Action:** Agent processes raw input dispatch in Trust Mode
- **Expected:**
  - [ ] All references to autonomous operation cite "Trust Mode (C9)" — not "Autonomous Mode"
  - [ ] Auto-promotion to Stable requires all 4 conditions: (a) no RULES.md conflicts, (b) no circular deps, (c) layer constraints satisfied, (d) spec content complete per template
  - [ ] No vague qualifiers ("crystal clear", "high-confidence") used in decision logic
  - [ ] Summary appended: `[Auto-SDD] {Spec} promoted to Stable; updated registry.`
- **Guards tested:** Trust Mode (C9) terminology consistency, quantified promotion criteria

### T142 — C12 Cascade: Spec Workflow Modifies INDEX, Task Workflow Does Not

- **Workflow:** `spec.md` + `task.md` (C12 interaction)
- **Synthetic State:**
  - `installer-architecture.md` (L1, Stable) demoted to RFC via `spec.md`
  - `installer-node.md` (L2, Implements: installer-architecture.md, Stable)
  - `TASKS.md` has active tasks for `installer-node.md`
- **Test 1 — spec.md C12 cascade:**
  - **Action:** Agent completes L1 status change in `spec.md`
  - **Expected:**
    - [ ] `INDEX.md` updated: `installer-node.md` status set to `RFC`
    - [ ] File header of `installer-node.md` updated to match
    - [ ] Report: "C12 Cascade: 1 dependent quarantined: [installer-node.md]."
- **Test 2 — task.md reacts to INDEX.md state:**
  - **Action:** `/magic.task update` triggered after C12 cascade
  - **Expected:**
    - [ ] `task.md` reads `INDEX.md`, sees `installer-node.md` = RFC
    - [ ] Tasks for `installer-node.md` marked `Blocked [!]` with reason: "L1 parent `installer-architecture.md` is `RFC` (C12)"
    - [ ] `installer-node.md` moved to `## Backlog` in `PLAN.md`
    - [ ] `task.md` does **NOT** modify `INDEX.md` (read-only for status)
- **Guards tested:** C12 ownership (spec.md writes INDEX, task.md reads only), cascade behavioral contract

### T143 — Rule Workflow Pre-flight HALT on Checksum Mismatch

- **Workflow:** `rule.md` (§Operational Logic — Pre-flight)
- **Synthetic State:**
  - `.magic/.checksums` has been manually altered (hash mismatch)
  - `check-prerequisites --json` returns `checksums_mismatch: true`
- **Action:** `/magic.rule add "New convention"` triggered
- **Expected:**
  - [ ] Pre-flight runs `check-prerequisites --json`
  - [ ] Agent detects `checksums_mismatch`
  - [ ] **HALT** with report: "Engine integrity failure. Run `update-engine-meta` or restore from origin."
  - [ ] No rule proposal is shown
  - [ ] No RULES.md modification occurs
- **Guards tested:** Rule pre-flight HALT condition, engine integrity gate

### T144 — Init Handles Unrecognized Pre-flight Failure

- **Workflow:** `init.md` (Step 1 — unrecognized failure branch)
- **Synthetic State:**
  - `check-prerequisites --json` returns `ok: false` with an unknown field: `{"ok": false, "unknown_error": "disk_full"}`
  - No `ENGINE_INTEGRITY`, no `GHOST_REGISTRY`, no missing system files
- **Action:** Calling workflow triggers init
- **Expected:**
  - [ ] Agent recognizes `ok: false` without matching any known failure category
  - [ ] **HALT** with report: "Unexpected pre-flight failure: {raw output}. Investigate manually."
  - [ ] Agent does NOT proceed to Step 2 (Init)
  - [ ] Agent does NOT silently ignore the failure
- **Guards tested:** Init else-branch for unrecognized failures, fail-safe HALT

### T145 — Spec Deprecation Cascade Flags Stale Implements Link

- **Workflow:** `spec.md` (Updating — Deprecation Cascade)
- **Synthetic State:**
  - `auth-concept.md` (Stable L1), `auth-impl.md` (Stable L2, Implements: auth-concept.md), `auth-tests.md` (Stable L2, Related Specifications: auth-concept.md)
- **Action:** User says "Deprecate auth-concept.md"
- **Expected:**
  - [ ] `auth-concept.md` status → Deprecated, INDEX.md updated — deprecation proceeds without blocking
  - [ ] Deprecation Cascade scans INDEX.md for `Implements: auth-concept.md` → finds `auth-impl.md`
  - [ ] Report: "L2 `auth-impl.md` has no valid L1 parent — `auth-concept.md` is Deprecated."
  - [ ] Deprecation Cascade scans for `Related Specifications` referencing `auth-concept.md` → finds `auth-tests.md`
  - [ ] Report: "`auth-tests.md` references Deprecated spec `auth-concept.md` in Related Specifications."
  - [ ] Post-Update Review surfaces findings as actionable warnings with suggested commands (`→ /magic.spec amend` or `→ /magic.spec deprecate`)
  - [ ] Deprecation is NOT blocked by dependent specs — non-blocking cascade
- **Guards tested:** Deprecation Cascade (Implements + Related), non-blocking report via Post-Update Review

### T146 — Rule Remove Dependency Scan Warns on Referenced Convention

- **Workflow:** `rule.md` (Remove — Dependency Scan)
- **Synthetic State:**
  - RULES.md §7 C5: "All specs must use kebab-case filenames"
  - `analyze.md` Mode C step 3 references "kebab-case convention" with C5 check
- **Input:** `"Remove rule C5"`
- **Expected:**
  - [ ] Before proposing, agent scans `.magic/*.md` and `.design/` for `C5` references
  - [ ] Reference found in `analyze.md`
  - [ ] Propose step includes dependency warning: "Convention `C5` is referenced by: [analyze.md: Mode C Structural Integrity]. Removing it may break workflow logic or spec compliance."
  - [ ] Single "Current vs Proposed" approval — no additional confirmation gate
  - [ ] If approved → C5 deleted, Major version bump
- **Guards tested:** Remove Dependency Scan integrated into Propose step (no extra gate)

### T147 — Run Handoff Succession Returns to Task Update

- **Workflow:** `run.md` (Step 4 — Handoff)
- **Synthetic State:**
  - `TASKS.md` Phase 1 task `T-1A01` mapped to `auth.md`
  - During execution, spec is ambiguous → HALT triggered
- **Action:** Agent halts and triggers `magic.spec` update. Spec is updated successfully.
- **Expected:**
  - [ ] Agent records Blocked status with reason in TASKS.md
  - [ ] Agent triggers `magic.spec` update for `auth.md`
  - [ ] After spec update completes, agent returns to `magic.task update` to rebuild dependencies
  - [ ] Task validity re-verified before resuming execution
- **Guards tested:** Handoff succession chain (run → spec → task → run)

### T148 — Simulate HALT Includes Recovery Hint

- **Workflow:** `simulate.md` (Step 0: Pre-flight)
- **Synthetic State:**
  - `.magic/.checksums` exists but `run.md` checksum mismatches (file was modified)
- **Action:** `/magic.simulate run`
- **Expected:**
  - [ ] `check-prerequisites` reports `checksums_mismatch` for `run.md`
  - [ ] **HALT** — no simulation proceeds
  - [ ] Report includes recovery hint: `update-engine-meta --workflow {mismatched_workflow}` or restore from origin
  - [ ] Agent does NOT fall through to any mode
- **Guards tested:** Simulate pre-flight HALT with actionable recovery hint

### T149 — Rule Core-Amendment Routing Gate

- **Workflow:** `rule.md` (Guards — Core-Amendment Routing)
- **Synthetic State:**
  - RULES.md: §3 Layer Rules contain "L2 cannot enter RFC until L1 is Stable"
- **Input:** `"Change rule: L2 can enter RFC regardless of L1 status"`
- **Expected:**
  - [ ] Agent identifies target: §3 (core section)
  - [ ] Core-Amendment Routing activates: "This targets core section §3. Core amendments require explicit approval and trigger a Major version bump."
  - [ ] User must explicitly confirm
  - [ ] If denied → abort, no changes
  - [ ] If confirmed → §3 updated, RULES.md Major version bump
- **Guards tested:** Core-Amendment Routing gate, explicit approval requirement

### T150 — Analyze Mode A Proposal Shows Explicit Options

- **Workflow:** `analyze.md` (Mode A — Proposal step)
- **Synthetic State:**
  - `.design/INDEX.md` empty, project has `src/` with 30 files
- **Action:** `/magic.analyze` → Mode A generates proposal with 4 L1 specs and 3 RULES.md entries
- **Expected:**
  - [ ] Proposal presented with explicit option set: (a) Approve all, (b) Select, (c) Adjust, (d) Cancel
  - [ ] Agent waits for user choice — does NOT auto-dispatch
  - [ ] If user picks (b) Select → individual items shown for approval
  - [ ] If user picks (d) Cancel → no files created, no INDEX.md changes
- **Guards tested:** Defined approval option set, wait-for-choice gate

### T151 — Analyze Priority 1 Prints Workspace Confirmation

- **Workflow:** `analyze.md` (§Workspace Resolution — Priority 1)
- **Synthetic State:**
  - `workspace.json`: `engine` (default), `installers`. Both valid.
- **Action:** `/magic.analyze installers`
- **Expected:**
  - [ ] Workspace resolved to `installers` via Priority 1 (explicit arg)
  - [ ] Agent prints: "Active workspace: installers."
  - [ ] Default `engine` workspace is NOT used despite being set as default
  - [ ] Analysis scoped to `installers` workspace paths
- **Guards tested:** Priority 1 override, confirmation print

### T152 — Run Mid-Run HALT Notifies Manager in Parallel Mode

- **Workflow:** `run.md` (Step 4 — Mid-Run Stability Check, Parallel mode)
- **Synthetic State:**
  - Parallel mode. Track A executing `T-1A01` for `auth.md` (Stable at dispatch).
  - Track B triggers spec amendment → `auth.md` drops to RFC mid-execution.
  - Track A reaches Step 4 and attempts to commit Done.
- **Expected:**
  - [ ] Track A re-reads INDEX.md, detects `auth.md` is now RFC
  - [ ] **HALT** on Track A: "Spec `auth.md` demoted to RFC during execution of `T-1A01`."
  - [ ] `T-1A01` left as In Progress (NOT Done)
  - [ ] Developer Track A notifies Manager role of suspension
  - [ ] Manager halts further assignments for specs affected by `auth.md` demotion
- **Guards tested:** Mid-Run HALT, Manager notification in Parallel mode

### T153 — Task Argument Routing: Scoped Planning (Mode B)

- **Workflow:** `task.md` (Argument Routing)
- **Synthetic State:**
  - `workspace.json`: `{"default": "engine", "workspaces": {"engine": {}, "installers": {}}}`
  - `engine/INDEX.md`: 3 Stable specs.
  - `installers/INDEX.md`: 2 Stable specs.
- **Action:** User runs `/magic.task installers`
- **Expected:**
  - [ ] Argument parsed: `installers` matches workspace name → **Scoped Planning** (Mode B)
  - [ ] Only `installers/INDEX.md` is read for planning (not engine)
  - [ ] PLAN.md and TASKS.md written to `.design/installers/`
  - [ ] Engine workspace specs are NOT included in the plan
  - [ ] Handoff recommends `/magic.run installers` (workspace propagated)
- **Guards tested:** Argument Routing (Mode B), Workspace Scope Isolation (C15), Handoff Propagation

### T154 — Task Argument Routing: Guided Planning with Workspace Fallback (Mode C)

- **Workflow:** `task.md` (Argument Routing)
- **Synthetic State:**
  - `workspace.json`: `{"default": "engine", "workspaces": {"engine": {}, "installers": {}}}`
  - `engine/INDEX.md`: 3 Stable specs (2 API-related, 1 unrelated).
  - No `MAGIC_WORKSPACE` env var set.
- **Action:** User runs `/magic.task "only API specs"`
- **Expected:**
  - [ ] Argument parsed: text does not match any workspace → **Guided Planning** (Mode C)
  - [ ] **Workspace Fallback**: No workspace in arg, no env var → `workspace.json` default = `engine` used
  - [ ] Workspace resolved silently via Core Invariant #1 (Zero-Prompt)
  - [ ] Planning directive "only API specs" applied as filter within `engine` workspace
  - [ ] User is NOT prompted to select a workspace
- **Guards tested:** Argument Routing (Mode C), Workspace Fallback, Zero-Prompt Resolution

### T155 — Task Argument Routing: Disambiguation (Quoted Workspace Name)

- **Workflow:** `task.md` (Argument Routing)
- **Synthetic State:**
  - `workspace.json`: `{"default": "engine", "workspaces": {"engine": {}, "installers": {}}}`
- **Action:** User runs `/magic.task "engine"`
- **Expected:**
  - [ ] Argument parsed: quoted text → forced directive interpretation (NOT workspace selection)
  - [ ] Workspace resolved via default (`engine`) from `workspace.json`
  - [ ] Text "engine" treated as planning directive, not workspace selector
  - [ ] Agent interprets "engine" as focus/filter term for planning
- **Guards tested:** Disambiguation Rule (quotes override workspace match)

### T156 — Run Argument Routing: Targeted Task by ID (Mode C — T-XXXX)

- **Workflow:** `run.md` (Argument Routing)
- **Synthetic State:**
  - `workspace.json`: `{"default": "engine", "workspaces": {"engine": {}}}`
  - `engine/TASKS.md`: Phase 1 with T-1A01 (Todo), T-1A02 (Todo, dep: T-1A01), T-1B01 (Todo).
  - RULES.md §7 C3: Sequential mode.
- **Action:** User runs `/magic.run T-1A01` (unquoted, not a workspace name)
- **Expected:**
  - [ ] Argument parsed: `T-1A01` does not match any workspace → non-workspace token
  - [ ] Pattern matches `T-XXXX` → **Targeted Task** execution
  - [ ] Workspace resolved via default (`engine`) — Workspace Fallback applied
  - [ ] Only T-1A01 is executed (not the full phase)
  - [ ] Dependency check: T-1A01 has no deps → proceeds
- **Guards tested:** Argument Routing (Targeted Task), Non-workspace token detection, Workspace Fallback

### T157 — Run Argument Routing: Scoped + Directed Phase (Mode D)

- **Workflow:** `run.md` (Argument Routing)
- **Synthetic State:**
  - `workspace.json`: `{"default": "engine", "workspaces": {"engine": {}, "installers": {}}}`
  - `installers/TASKS.md`: Phase 1 (all Done), Phase 2 (3 Todo tasks).
  - RULES.md §7 C3: Parallel mode.
- **Action:** User runs `/magic.run installers "phase-2"`
- **Expected:**
  - [ ] Argument parsed: `installers` = workspace, `"phase-2"` = directed text → **Scoped + Directed** (Mode D)
  - [ ] Only `installers/TASKS.md` is read
  - [ ] Only Phase 2 tasks are targeted (Phase 1 skipped — already Done)
  - [ ] Manager Agent activated (Parallel mode) for Phase 2 tasks
  - [ ] Handoff (if re-planning needed) recommends `/magic.task installers`
- **Guards tested:** Argument Routing (Mode D), Phase targeting, Workspace scoping, Handoff Propagation

### T158 — Cross-Workflow Handoff Propagation with Scoped Argument

- **Workflow:** `task.md` → `run.md` (Handoff chain)
- **Synthetic State:**
  - `workspace.json`: `{"default": "engine", "workspaces": {"engine": {}, "installers": {}}}`
  - User completed `/magic.task installers` (Mode B — scoped planning).
  - Planning is done, handoff to run triggered.
- **Expected:**
  - [ ] task.md MANDATORY HARD STOP fires
  - [ ] Handoff message recommends: `/magic.run installers` (NOT `/magic.run`)
  - [ ] Workspace `installers` is explicitly included in the recommended command
  - [ ] If user follows recommendation and runs `/magic.run installers`, execution scopes correctly
- **Guards tested:** Handoff Propagation (task→run), Workspace context preservation across workflow boundary

### T159 — Spec T4 Tier Routing: Workspace Signal Detected

- **Workflow:** `spec.md` (Dispatching from Raw Input → T4 Inline Guards)
- **Synthetic State:**
  - Active workspace: `installers` (resolved via Zero-Prompt).
  - `.design/RULES.md`: §7 has C1–C10.
  - `.design/installers/RULES.md`: exists with WC1.
- **Input:** `"Add OAuth2 to auth spec. Remember that all installer packages must use semantic versioning."`
- **Expected:**
  - [ ] T4 trigger detected: "Remember that..."
  - [ ] **Tier Routing**: "installer packages" matches workspace signal → target = `.design/installers/RULES.md`
  - [ ] **Duplication Check**: scans both global C1–C10 and workspace WC1 for overlap → none found
  - [ ] Rule written to `.design/installers/RULES.md` as WC2 (NOT to global RULES.md)
  - [ ] Spec update and rule write grouped in single atomic proposal
- **Guards tested:** T4 Inline Tier Routing, workspace signal detection, atomic proposal

### T160 — Spec T4 Duplication Check Catches Overlap

- **Workflow:** `spec.md` (Dispatching from Raw Input → T4 Inline Guards)
- **Synthetic State:**
  - Active workspace: `engine`.
  - `.design/RULES.md` §7 has C7: "Universal Script Executor — all automation via `executor.js`."
- **Input:** `"Update engine-core spec. Remember that all scripts must go through executor.js."`
- **Expected:**
  - [ ] T4 trigger detected: "Remember that..."
  - [ ] **Tier Routing**: rule is universal (no workspace signal) → target = `.design/RULES.md`
  - [ ] **Duplication Check**: proposed rule semantically overlaps with existing C7
  - [ ] Agent surfaces overlap: "This overlaps with C7 (Universal Script Executor). Merge, replace, or add separately?"
  - [ ] No write to RULES.md until user decides
  - [ ] Spec update proceeds independently (rule and spec are separate approval tracks)
- **Guards tested:** T4 Inline Duplication Check, semantic overlap detection

### T161 — Spec T4 Constitutional Guard Blocks Contradicting Rule

- **Workflow:** `spec.md` (Dispatching from Raw Input → T4 Inline Guards)
- **Synthetic State:**
  - `.design/RULES.md` §5: "No implementation code — pseudo-code only."
- **Input:** `"Add Python examples to database spec. Remember that all specs must include runnable code samples."`
- **Expected:**
  - [ ] T4 trigger detected: "Remember that..."
  - [ ] **Constitutional Guard**: proposed rule ("runnable code samples") contradicts §5 ("No implementation code")
  - [ ] **HALT** on rule write: "Proposed rule contradicts §5 (Content Rules). Cannot apply."
  - [ ] Spec update (adding Python examples) also flagged as §5 violation
  - [ ] Neither rule nor spec change written
- **Guards tested:** T4 Inline Constitutional Guard, §1–6 protection

### T162 — Spec T4 Atomic Intent with Drift Resolution

- **Workflow:** `spec.md` (T4 + Version Drift Guard)
- **Synthetic State:** `INDEX.md` (v1.0), File Header (v1.1). VERSION_DRIFT active.
- **Input:** "Update spec X. Remember that Y."
- **Expected:**
  - [ ] T4 detected; RE-3 detected.
  - [ ] **HALT** before any write.
  - [ ] Intent "Remember that Y" is queued.
  - [ ] Rule is NOT written to RULES.md until drift is resolved.
  - [ ] After drift fix: rule and spec update applied atomically.
- **Guards tested:** T4 Queuing, RE-3 Atomicity.

```
**Test Suite Finalized** — v1.9.47 (Last: T162)
```
