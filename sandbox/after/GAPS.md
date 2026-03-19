# GAPS — Language Observations from SDD Translation

> Findings from translating a real-world Specification-Driven Development engine
> (`.magic/` — 8 workflows, ~2000 lines of Markdown) into NODUS `.nodus` format.
>
> Each entry is: **ID | Severity | Area | Gap | Suggested Fix**
>
> Severity: `BLOCKER` (cannot express correctly) | `WORKAROUND` (expressible but awkward) | `MISSING` (absent feature, needed) | `SUGGESTION` (improvement idea)

---

## G001 — MISSING — Commands — `READ_FILE()` not in core

**Problem:** `FETCH(target:url|str)` implies a URL or named source. Reading local
filesystem paths (e.g., `.design/RULES.md`) is a core SDD operation but lacks a
dedicated command. Using `FETCH()` for local paths works semantically but the
intent is ambiguous — a reader cannot distinguish network vs. disk fetches.

**Impact:** Every SDD workflow reads local files. Without clarity, agents may
incorrectly cache or proxy these reads.

**Fix:** Add `READ_FILE(path:str) → str|null` to `§commands` in `schema.nodus`
as a distinct primitive from `FETCH()`. Document: "FETCH for remote/named sources;
READ_FILE for local filesystem paths."

---

## G002 — MISSING — Commands — `SCAN_DIR()` absent

**Problem:** Project analysis (analyze.nodus), spec audits (spec.nodus), and
engine checks all require scanning directories for files. No such command exists
in core.

**Impact:** Cannot implement file coverage analysis, registry audits, or
workspace scans without this primitive.

**Fix:** Add `SCAN_DIR(path:str) +depth=int → list` to `§commands_system` or
core. Returns list of `{ name, path, type: "file"|"dir" }`.

---

## G003 — MISSING — Commands — `MOVE()` and `COPY()` absent from user commands

**Problem:** `MOVE()` and `COPY()` exist conceptually but aren't in `§commands`.
The SDD Archival step (C8) — moving `phase-N.md` to `archives/tasks/` — requires
`MOVE()`. `COPY()` is needed for template-based creation flows.

**Fix:** Add `MOVE(from:str, to:str) → bool` and `COPY(from:str, to:str) → bool`
to `§commands` (or `§commands_system`). Note: MOVE is destructive — document that
it requires confirmation in non-automated contexts.

---

## G004 — MISSING — Commands — `ENV(key:str)` absent

**Problem:** SDD's Workspace Resolution reads the `MAGIC_WORKSPACE` environment
variable (priority #2 in the resolution chain). No command exists in NODUS to
read environment variables.

**Impact:** The workspace priority chain cannot be faithfully implemented without
falling back to a workaround (e.g., passing env vars as `@in` fields, which breaks
the zero-prompt invariant).

**Fix:** Add `ENV(key:str) → str|null` to `§commands`. Returns the environment
variable value or null if not set.

---

## G005 — MISSING — Operators — No regex / pattern matching (`MATCHES`)

**Problem:** SDD argument routing requires detecting patterns like:
- `"T-1A01"` → matches `^T-[A-Z0-9]+`
- `"phase-2"` → matches `^phase-\d+`

The core `§operators` only define `= != < > <= >= CONTAINS NOT IN AND OR |`.
No pattern matching operator exists.

**Impact:** Argument routing tables in `run.nodus` and `task.nodus` are the most
critical dispatching logic in the engine. Without `MATCHES`, routing must rely on
`CONTAINS` heuristics (brittle) or be deferred to an ANALYZE() call (LLM-dependent,
not deterministic).

**Fix:** Add `MATCHES :: value matches regex pattern string` to `§operators`.
The SDD schema extension declares it locally in `§operators_sdd` as a workaround,
but it should be a core primitive.

---

## G006 — WORKAROUND — Control Flow — `HALT` vs `!BREAK` semantic distinction

**Problem:** The before/ workflows use **HALT** for fatal, blocking stops with an
error report (e.g., engine integrity failure, circular dependency). `!BREAK` in NODUS
means "stop current workflow" but carries no built-in severity signal.

**Impact:** HALT-level stops are mapped to `ESCALATE(human)` + `!BREAK`, which is
correct in effect but verbose. The semantic richness (HALT = catastrophic, !BREAK
= controlled exit) is lost in the output status — both produce `ABORTED`.

**Suggestion:** Add `!HALT` as a new control keyword: fatal stop that always sets
`status = FAILED` (not `ABORTED`) and requires `ESCALATE()` to be called first.
Or: allow `!BREAK` to accept a severity level: `!BREAK fatal`, `!BREAK soft`.

---

## G007 — BLOCKER — State — No stateful counter across workflow invocations

**Problem:** `spec.md` has a "Periodic Registry Audit" that triggers every 5th
spec write operation (per conversation). This requires a persistent counter that
increments across workflow invocations within a session.

**Impact:** Cannot faithfully implement this guard. In NODUS, `$memory` (session
scope) persists within a session — but there is no way to increment a counter
automatically on each invocation without an explicit `RECALL → increment → REMEMBER`
pattern that must be manually coded into every spec write sub-workflow.

**Workaround used:** Dropped the "every 5th" trigger; replaced with "manual audit
command" (always available, never auto-triggered). Logic semantics preserved, but
the auto-trigger frequency is lost.

**Fix:** Add an `@ON: counter:N` trigger syntax, or add `COUNTER(key:str) +increment=int`
as a command that returns the current count. Or: support `!PREF: trigger_on_count:5`
as a workflow-level preference.

---

## G008 — WORKAROUND — Parallel Mode — Manager/Developer role distinction

**Problem:** `run.md` Parallel mode has explicit roles: **Manager** (orchestrator,
assigns tracks, syncs PLAN.md) and **Developer** (track owner, executes in order,
reports Done/Blocked). This multi-agent role pattern is important for real parallel
execution coordination.

**Impact:** NODUS `~PARALLEL` executes branches concurrently but has no built-in
role concept. The Manager/Developer distinction must be expressed via agent assignment
in `§runtime.agents`, but `§runtime.agents` only maps roles to model names — not
to workflow sub-roles within `~PARALLEL` blocks.

**Suggestion:** Add a `~PARALLEL +role=manager` / `+role=developer` syntax, or
allow `§runtime.agents` to map to workflow-scoped roles: `{ manager: "claude-opus-4",
developer: "claude-sonnet-4" }` and reference them inside `~PARALLEL` blocks.

---

## G009 — MISSING — Commands — `TRANSPILE()` undeclared in schema

**Problem:** `cli.nodus` uses `TRANSPILE($source) +from=nodus +to=human` but
`TRANSPILE()` is not declared in `§commands`. It exists in the CLI workflow as if
it's a primitive, but has no formal definition in `schema.nodus`.

**Fix:** Add `TRANSPILE(input:str) +from=str +to=str → str` to `§commands`.
Semantics: convert between NODUS machine format and HUMAN MODE comment format.

---

## G010 — MISSING — Commands — `VERSION_BUMP()` and `GEN_CONTEXT()` absent

**Problem:** `run.md`'s plan completion (Succession Loop) requires:
1. Bumping version in manifests (`package.json`, `pyproject.toml`)
2. Regenerating `CONTEXT.md`

Neither operation has a NODUS primitive. Both are project-specific operations
that shouldn't be hardcoded as GEN() calls.

**Fix:** These are defined in `sdd.schema.nodus` as SDD extensions. However,
they feel generic enough for `§commands_system`: `VERSION_BUMP(type:str) +manifests=list`
and `GEN_CONTEXT()`. The latter could be generalized as
`GENERATE_DOC(template:str) → bool`.

---

## G011 — WORKAROUND — Triggers — `@ON:` lacks workspace-scoped priority

**Problem:** `run.md` argument routing has a disambiguation rule: "if a single
unquoted word matches both a workspace name and a directive keyword, workspace takes
priority." This disambiguation cannot be expressed in `@ON:` triggers — they match
in declaration order, not semantic priority.

**Workaround used:** Parse argument in `@steps:0` via `ANALYZE()` into a `$cmd.mode`
variable first, then route via `@ON: $cmd.mode = "..."`. This works but adds an
LLM-mediated step to what should be deterministic routing.

**Suggestion:** Allow `@ON:` to declare priority: `@ON(priority=1): ...` or support
a `@DISPATCH:` block with ordered, conditional routing (like a `match` statement).

---

## G012 — MISSING — Commands — `PARSE_MD_HEADER()` and `PARSE_INDEX()` absent

**Problem:** SDD's Version Drift Guard, File-Header Parity checks, and C12 Cascade
all require extracting structured data from Markdown files (YAML-like headers and
registry tables). No NODUS primitive does this.

**Impact:** These guards are critical safety mechanisms. Without structured parsing,
they rely on `ANALYZE()` (LLM extraction), which is non-deterministic.

**Fix:** Add `PARSE_MD_HEADER(path:str) → obj` and `PARSE_INDEX(path:str) → index_obj`
as deterministic (non-LLM) parsing commands in `§commands_system`. These should be
regex/parser-based, not AI-based, for reliability.

---

## G013 — SUGGESTION — Types — No `date_expr` type or `DATE()` function

**Problem:** Multiple workflows use `$session.ts_start` for the current date in
document headers (templates, RETROSPECTIVE.md entries, CHANGELOG entries). There is
no way to format, compare, or manipulate timestamps beyond storing ISO strings.

**Suggestion:** Add `DATE(format:str) → str` command and a `date_expr` type that
supports arithmetic (e.g., `DATE() - 30 days` for "last 30 days" in analyze.md
high-churn detection). Currently high-churn detection is not expressible in NODUS.

---

## G014 — WORKAROUND — Schema — No `workspace.json` format defined in schema

**Problem:** All SDD workflows read `.design/workspace.json` but its format is
not defined anywhere in the NODUS schema. The structure `{ workspaces:[], default:str }`
is implied but not validated.

**Impact:** An agent loading the schema has no contract for this file. It may
parse it differently or infer the wrong structure.

**Fix:** Add `workspace_config` type to `§types` or the SDD schema:
```
workspace_config { workspaces: list[workspace_cfg], default: str|null }
workspace_cfg    { name: str, path: str, scope: list, default: bool }
```

---

## G015 — SUGGESTION — Schema — `§wf` header `compatible` versions not enforced

**Problem:** `§meta { compatible: ["0.1", "0.2", "0.3"] }` in `schema.nodus`
declares backward-compatible versions but there's no lint rule (E013?) that
checks whether a workflow's declared version is in the `compatible` list.

**Fix:** Add lint rule `E013 :: error — workflow version not in schema.compatible list`.

---

## G016 — SUGGESTION — Lint — No lint rule for `~PARALLEL` without error isolation

**Problem:** `~PARALLEL` branches can independently fail, but there's no rule
requiring per-branch error handling. In SDD Parallel mode, a Developer track
suspending (spec demoted mid-run) must notify the Manager without killing other tracks.
Currently nothing enforces this pattern.

**Fix:** Add lint warning `W011 :: warn — ~PARALLEL block has no per-branch ?IF error
check`. Each branch in `~PARALLEL` should handle its own failure rather than relying
only on `~JOIN` to surface errors.

---

## G017 — WORKAROUND — Control Flow — `HALT` in Trust Mode auto-stop after dispatch

**Problem:** `spec.md` has a "HARD STOP" after raw-input dispatch: the agent MUST
halt and wait for user reply before proceeding to task generation. This is stronger
than `!BREAK` (which just stops the workflow) — it requires the next step to be
explicitly user-triggered, not auto-continued by an orchestrator.

**Impact:** In an orchestrated multi-agent pipeline, `!BREAK` returns control to
the orchestrator, which may immediately route to `sdd.task` without user input,
violating the HARD STOP invariant.

**Suggestion:** Add a `!PAUSE` control keyword: suspend workflow and require
explicit human re-trigger (not just agent continuation). Distinguished from
`!BREAK` (terminates) and `WAIT()` (time-based pause).

---

## G018 — SUGGESTION — Git Integration — No `GIT()` command

**Problem:** `analyze.md` Mode B (Re-Analysis) identifies "high-churn directories"
as `"≥10 commits in the last 30 days without spec coverage"`. This requires reading
git history, which has no NODUS primitive.

**Impact:** The high-churn coverage advisory (Advisory Report §Coverage Strategy)
is not implementable in NODUS without a git integration command.

**Fix:** Add optional `GIT(subcommand:str) +args=list → any` command, or a
`QUERY_GIT(query:str) → list` for structured git history queries. Mark as optional
(runtime error if git not available in environment).

---

## G019 — WORKAROUND — Testing — `suite.md` vs embedded `@test` blocks

**Problem:** The before/ system has a dedicated `tests/suite.md` with all test
scenarios in a single file (for batch simulation). NODUS's `@test:` blocks live
*inside* the workflow file they test — distributing tests across files.

**Impact:** `sdd.simulate.test_suite` must read `suite.md` as a separate file,
but in pure NODUS style, tests should be in workflow files. Running `nodus test`
across all workflow files achieves the same result, but the `simulate test` mode
references a physical `suite.md` that no longer exists in the same form.

**Resolution:** The SDD after/ distributes tests into each `.nodus` file as `@test:`
blocks. The `simulate.nodus` test suite mode falls back to `nodus test` behavior.
`suite.md` is deprecated in favor of native `@test:` distribution.

---

## G020 — MISSING — Schema — No checksum / hash primitive

**Problem:** Engine integrity (C14) compares checksums of `.nodus/` files against
a `.checksums` reference. `CHECK_PREREQS()` wraps this in the SDD schema, but
the underlying hash operation has no NODUS equivalent.

**Impact:** The checksum mechanism is entirely opaque — agents cannot compute,
verify, or update checksums in a standardized way. Everything goes through
`CHECK_PREREQS()` and `UPDATE_ENGINE_META()` as black-box SDD commands.

**Fix:** Add `HASH(value:str|file, algo:str) → str` to `§commands_system`.
Algorithms: `md5 | sha256 | sha1`. This would allow transparent checksum
verification in user workflows, not just SDD engine internals.

---

## SUMMARY

| ID   | Severity   | Short Description                              |
|------|------------|------------------------------------------------|
| G001 | MISSING    | READ_FILE() not in core                        |
| G002 | MISSING    | SCAN_DIR() absent                              |
| G003 | MISSING    | MOVE() / COPY() absent from user commands      |
| G004 | MISSING    | ENV() absent — can't read env vars             |
| G005 | MISSING    | MATCHES operator — no regex matching           |
| G006 | WORKAROUND | HALT vs !BREAK semantic distinction            |
| G007 | BLOCKER    | No stateful counter across invocations         |
| G008 | WORKAROUND | Manager/Developer role pattern in ~PARALLEL    |
| G009 | MISSING    | TRANSPILE() undeclared in schema               |
| G010 | MISSING    | VERSION_BUMP() and GEN_CONTEXT() absent        |
| G011 | WORKAROUND | @ON: lacks workspace-scoped routing priority   |
| G012 | MISSING    | PARSE_MD_HEADER() / PARSE_INDEX() absent       |
| G013 | SUGGESTION | No DATE() function or date arithmetic          |
| G014 | WORKAROUND | workspace.json format not defined in schema    |
| G015 | SUGGESTION | Compatible version not lint-checked            |
| G016 | SUGGESTION | No lint rule for ~PARALLEL error isolation     |
| G017 | WORKAROUND | No !PAUSE — HARD STOP weaker than intended     |
| G018 | SUGGESTION | No GIT() command for history-based analysis    |
| G019 | WORKAROUND | suite.md vs distributed @test: blocks          |
| G020 | MISSING    | No HASH() / checksum primitive                 |

---

## WHAT WORKED WELL

1. **`!!NEVER` / `!!ALWAYS` rules** — perfectly captured Core Invariants from every workflow.
   The 1:1 mapping is clean and complete.

2. **`!PREF:`** — captured soft behavioral preferences (trust mode, verbosity level,
   halt vs. guess) naturally. The `IF condition` clause handles context-dependent prefs.

3. **`@ON:` trigger routing** — the pre-parse-in-step-0 + `@ON: $cmd.mode = "..."`
   pattern cleanly handles all 6 argument routing modes from `run.md`.

4. **`~PARALLEL` / `~JOIN`** — cleanly expressed the parallel artifact verification
   in `init.nodus` (5 concurrent FILE_EXISTS checks). Significantly more readable than
   the markdown equivalent.

5. **`@macro:`** — `RESOLVE_WORKSPACE`, `ENGINE_PREFLIGHT`, `HEADER_PARITY_CHECK`
   eliminated massive duplication across all 8 workflows. This is the most impactful
   NODUS feature for SDD translation.

6. **`@test:` blocks** — tests from `suite.md` distributed into their native workflows.
   Happy path + guard case coverage per workflow. Much better locality than a monolithic
   suite file.

7. **Schema extension (`sdd.schema.nodus`)** — the `§schema:sdd` extension pattern
   cleanly namespaces all SDD-specific additions without polluting core. The `extends:`
   list in `§runtime` is clean.

8. **Lint rules (`§lint`)** — the existing E001-E012 / W001-W010 rules would catch
   most structural mistakes in the SDD workflows (missing @err, no @test, undefined vars).

9. **`ESCALATE(human)`** — natural mapping for all HALT conditions. The `+msg=` parameter
   carries the exact user-facing error message from the original workflows.

10. **`§wf:sub-workflow`** — nested sub-workflow declarations within a single file cleanly
    represent the multi-mode structure (analyze Modes A/B/C/D, run Sequential/Parallel,
    simulate test/direct/improv) without requiring separate files for each sub-mode.
