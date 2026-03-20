# Retrospective Workflow

Feedback loop for SDD engine health. Diagnoses bottlenecks without altering core design files.

## Core Invariants (Mandatory)

1. **Context (Zero-Prompt)**: Auto-resolve workspace via `.design/workspace.json`. Route all logic to `.design/{workspace}/`. Never ask.
2. **Read-only Analysis**: Gather data from `.design/` artifacts. NEVER modify specs, plans, or tasks. Write ONLY to `RETROSPECTIVE.md`.
3. **Auto-Init**: If `.design/` missing, auto-run `.magic/init.md`.
4. **Actionable Output**: Recommendations must be concrete (e.g., "Add guard X", "Remove step Y"). No abstract advice.
5. **Level Separation**: L1 (Snapshot) is silent and fast. L2 (Full) is deep and analytical.
6. **Engine Integrity (C14)**: If engine files (`.magic/`) modified → `node .magic/scripts/executor.js update-engine-meta --workflow retrospective` (Smart History: redundant automated entries are skipped).

## Workflow: Feedback & Metrics

| Level | Goal | Trigger | Output |
| :--- | :--- | :--- | :--- |
| **L1** | Mini-snapshot | Phase Complete (All Tasks Done) | Snapshots Table Row + Archival (C8) |
| **L2** | Full Audit | Plan Complete or Manual Command | Deep Analysis + Recommendations |

### Operational Logic (L1 & L2)

1. **Pre-flight**: `node .magic/scripts/executor.js check-prerequisites --json`.
2. **Collect**:
    - **Inventory**: INDEX.md status counts (D/R/S) & spec count.
    - **Health**: TASKS.md Done/Blocked/Cancelled summary per phase.
    - **Growth**: RULES.md §7 entry count & history scan.
    - **Drift**: Cross-reference INDEX ↔ PLAN ↔ TASKS for orphans/phantoms.
3. **Analyze (L2 Only)**:
    - **Efficiency**: Spec revisions-to-Stable ratio.
    - **Friction**: Recurrent blocking reasons in phase notes.
    - **Deep Registry Audit**:
        - **Shadow Logic**: Cross-reference `.design/specifications/` with actual codebase. Trace any implemented logic back to a `Stable` spec.
        - **Integrity**: Check if `INDEX.md` statuses truly reflect file content (e.g., if a file says `Draft` but is fully implemented).
    - **Signal**: Calculate from phase metrics:
      - 🟢 **Green**: `Blocked / Total < 0.1` AND 0 orphans/phantoms AND 0 shadow logic findings.
      - 🟡 **Yellow**: `0.1 ≤ Blocked / Total ≤ 0.2` OR 1-2 non-critical drift items (stale refs, minor version mismatches).
      - 🔴 **Red**: `Blocked / Total > 0.2` OR any shadow logic detected OR any critical registry inconsistency.
    - **DORA Metrics**: Collect `Deployment Frequency` and `Change Failure Rate` (Manual Input / External Hook required).
4. **Report**: Append to `RETROSPECTIVE.md` (Create from `.magic/templates/retrospective.md` if missing).

### Snapshot (L1) Execution

- **Step**: Append row to Snapshots table: `| Date | Phase N | D/R/S | Done/Blk/Can | Rules | Signal |`.
- **Archival (C8)**: Move `tasks/phase-N.md` → `archives/tasks/`. Update link in `TASKS.md` to use **relative** path.

## Retrospective Completion Checklist

```
Retro Checklist — {Level}
  ☐ Context: Zero-Prompt resolution; only RETROSPECTIVE.md modified
  ☐ Data: INDEX (statuses), PLAN (coverage), TASKS (metrics) analyzed
  ☐ DORA Metrics: Delivery performance (DF/CFR) recorded for L2
  ☐ Deep Audit: Shadow logic and Logic-to-Spec parity verified
  ☐ L1: Snapshot row appended; Phase N archived to archives/tasks/ (C8)
  ☐ L2: Actionable recommendations mapped to evidence; trends calculated
  ☐ Integrity: No speculative claims; all findings reference specific files
  ☐ Engine Meta: C14 bump if .magic/ files modified
```
