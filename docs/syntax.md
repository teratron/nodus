# NODUS Syntax & Grammar

This document provides a detailed breakdown of the NODUS symbolic syntax.

## 1. Declarations

### `§` — Section / Block

Declares a named block or file-level metadata.

```nodus
§wf:workflow_name v1.0
§schema:nodus v0.1
```

### `§runtime:` — Environment Block

Always the **second** block in a workflow file. Resolved before rules and steps.

```nodus
§runtime: {
  core:    .nodus/core/schema.nodus
  extends: [.nodus/schema/brand_voice.nodus]
  mode:    production
}
```

### `@ON:` — Triggers

Defines activation conditions. Multiple triggers are evaluated top-to-bottom.

```nodus
@ON: new_mention → RUN(wf:beautiful_mention)
@ON: sentiment < 0.2 → RUN(wf:crisis)
@ON: schedule:09:00  → RUN(wf:morning_digest)
```

### `@in:` / `@out:` — Input/Output

Defines the data contract for the workflow. `?=` denotes optional parameters with defaults.

```nodus
@in:  { username: str, force?: bool = false }
@out: $result
```

### `@ctx:` — Context Loader

Loads static context files into scope before execution.

```nodus
@ctx: [brand_voice, tone_guidelines]
```

### `@err:` — Error Handler

Declares what to do if any step raises an unhandled error.

```nodus
@err: ESCALATE(human)
```

### `@macro:` — Reusable Command Chain

Defines a named, reusable sequence of steps. Called with `RUN(@macro:name)`.

```nodus
@macro:reply
  1. TONE($pref.tone)
  2. GEN(reply) +ctx=$meta → $draft
  3. VALIDATE($draft) ^brand_voice → $validated
@end
```

### `@test:` — Inline Test Block

Defines a test case attached to the workflow. Tags group tests by purpose.

```nodus
@test: happy_path +tag=smoke
  @in: { post_url: "https://example.com/post" }
  @expect: $out.status = "published"
```

### `;` / `;;` — Comments

Single-line comments ignored by the parser.

```nodus
;; Workflow: beautiful_mention
;; Purpose: respond to positive social mentions
; inline comment after a step
```

## 2. Constraints & Preferences

### `!!` — Absolute Rules

Inviolable hard constraints. If a step violates a `!!` rule, execution stops immediately with `NODUS:RULE_VIOLATION`.

```nodus
!!NEVER: publish WITHOUT prior validation
!!ALWAYS: log($out)
!!NEVER: ROUTE(external) IF $data.type = confidential
```

### `!PREF:` — Soft Preferences

Defaults for ambiguous situations. Can be overridden by step-level modifiers.

```nodus
!PREF: tone = brand_voice OVER tone = user_request
!PREF: brevity OVER completeness IF channel = twitter
```

## 3. Flow Control

### `→` — Pipeline Operator

Passes the output of the left side as the value of the right side (variable assignment).

```nodus
FETCH($url) → $raw
ANALYZE($raw) ~sentiment ~intent → $meta
```

### `?IF / ?ELIF / ?ELSE` — Conditionals

Supports operators: `<`, `>`, `=`, `!=`, `>=`, `<=`, `CONTAINS`, `IN`, `NOT`, `AND`, `OR`, `MATCHES`.

```nodus
?IF $sentiment < 0 → TONE(empathetic)
?ELIF $sentiment < 0.5 → TONE(neutral)
?ELSE → TONE(warm)
```

Nested conditionals are allowed up to 3 levels deep. Beyond that, extract into a sub-workflow.

### `?SWITCH` — Multi-Branch Dispatch

Cleaner alternative to `?IF / ?ELIF` chains when branching on a single scalar value.

```nodus
?SWITCH $cmd.mode:
  "ventilate" → RUN(wf:mode_c)
  "delta"     → RUN(wf:mode_b)
  "focused"   → RUN(wf:mode_d)
  *           → ESCALATE(human) +msg="Unknown mode: $cmd.mode"
```

- Arms are evaluated top-to-bottom; first match wins, no fallthrough.
- `*` is the wildcard (default) arm — optional but strongly recommended (lint W012).
- If no arm matches and `*` is absent — emits `NODUS:SWITCH_NO_MATCH` (warn), continues.
- For multi-step arms: use `ROUTE(wf:name)`.

### `!BREAK` / `!SKIP` / `!HALT` / `!PAUSE` — Execution Control

| Keyword | Status set | Can auto-resume? | Use when |
| :--- | :--- | :--- | :--- |
| `!BREAK` | ABORTED | Yes (orchestrator) | Controlled exit — gate done, dry-run done |
| `!SKIP` | — | — | Skip current loop iteration |
| `!HALT` | FAILED | No | Fatal unrecoverable error |
| `!PAUSE` | PAUSED | No (human only) | Mandatory approval gate |

```nodus
?IF $meta.sentiment < 0.2 → ROUTE(wf:crisis) !BREAK
~FOR $item IN $list:
    ?IF $item.skip = true → !SKIP
    PROCESS($item) → $result
~END

;; fatal stop — requires ESCALATE() in same step
ESCALATE(human) +msg="Integrity check failed"
!HALT

;; hard stop awaiting human re-trigger
!PAUSE
```

`!HALT` requires `ESCALATE()` to be called in the same step.
`!PAUSE` suspends the workflow; orchestrators **must not** auto-resume it.

### `~FOR / ~UNTIL` — Loops

All loops must be closed with `~END`. `~UNTIL` requires `MAX:n`.

```nodus
~FOR $item IN $mentions:
    PROCESS($item) → $result
    APPEND($result → $out)
~END

~UNTIL $quality > 0.85 | MAX:3:
    REFINE($draft) → $draft
~END
```

### `~MAP` — Collection Transform

Single-line transform: applies one command to every item and collects results.

```nodus
~MAP $specs:     SCORE($it) ^confidence    → $scores
~MAP $dirs:      ANALYZE($it) ~topics      → $topic_lists
```

- `$it` is the implicit current item.
- If collection is empty — result is `[]`, never errors.
- For multi-step transforms per item, use `~FOR / APPEND` instead.

### `~RETRY:n` — Step-Level Retry

Re-executes a step up to `n` times on failure before propagating the error.

```nodus
FETCH($url) ~RETRY:3 → $raw
FETCH($url) ~RETRY:3 +backoff=2 → $raw
GEN(report) ~RETRY:2 +retry_on=null → $draft
```

- `n` is mandatory — `~RETRY` without `:n` is lint error E014. Maximum: 10.
- Default retry condition: `error`. Use `+retry_on=null` or `+retry_on=both` as needed.
- `+backoff=int`: seconds to wait between attempts (default: 0).
- After `n` retries without success — step fails, triggers `@err` normally.

### `~PARALLEL / ~JOIN` — Concurrency

Executes branches concurrently. `~JOIN` collects all outputs into a single object.

```nodus
~PARALLEL:
    ANALYZE($text) ~sentiment → $s
    ANALYZE($text) ~intent    → $i
    ANALYZE($text) ~entities  → $e
~JOIN → $meta
```

## 4. Variables, Constants & Expressions

### `$` — Variables

Variables are assigned via `→` and scoped to the workflow. See [schema.md](schema.md) for reserved variables.

```nodus
$raw, $meta, $out, $error, $draft
```

### `$.` — Optional Chaining

Short-circuits to `null` if any segment in the path is `null` or undefined.
Does **not** trigger `NODUS:UNDEFINED_VAR`.

```nodus
ANALYZE($ws_config?.workspaces) → $scope
?IF $user?.preferences?.theme = "dark":
NOTIFY(human) +msg="Agent: $session?.agent_id"
```

Combine with `??` null coalescing: `$user?.tier ?? "free"`

### `WHERE / FIRST / LAST` — Collection Expressions

Inline filtering and access without a `~FOR` block.

```nodus
;; filter — returns a new list; $it is the implicit item variable
$delta.covered WHERE $it.drift_score > 0.3 → $sync_candidates
$log WHERE $it.level = "error"             → $errors

;; access — returns a single item or null
FIRST($items WHERE $it.active = true) → $first_active
LAST($log WHERE $it.level = "error")  → $last_error
FIRST($collection) → $head
```

Returns `[]` (WHERE) or `null` (FIRST/LAST) when nothing matches — never errors.
For complex multi-step filtering, use `~FOR` instead.

### String Interpolation

`$var` and `$obj.field` are expanded inside string literals before the step executes.

```nodus
NOTIFY(human) +msg="Found $gaps.count issues in $workspace"
ASK("Review $spec.name version $spec.version?") → $ok
```

- Resolved by the runtime — not by LLM.
- Works in: `+msg`, `+hint`, `NOTIFY()`, `ASK()`, `CONFIRM()`, `GEN()` string params.
- Escape with `\$` to suppress: `"cost: \$5"` → outputs `"cost: $5"`.

### `$CFG.*` — Global Constants

Constants defined in `.nodus/config.nodus`. Read-only at workflow runtime.

```nodus
$CFG.CRISIS_THR = -0.5
$CFG.MAX_REPLY_LEN = 280

; use in workflow:
?IF $meta.sentiment < $CFG.CRISIS_THR → ROUTE(wf:crisis) !BREAK
```

## 5. File References & Imports

NODUS has two levels of file references: **static** (resolved before execution) and **dynamic** (resolved at runtime).

### Static Imports

Declared in the `§runtime:` block. Resolved once when the agent boots.

```nodus
§runtime: {
  core:    .nodus/core/schema.nodus
  extends: [.nodus/schema/sdd.schema.nodus]
  @needs:  [§commands_sdd, §macros_sdd, §types_sdd]
  mode:    production
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `core:` | path | Path to `schema.nodus`. Must resolve or execution halts (E011). |
| `extends:` | path[] | Additional schema files loaded in order. Missing files raise W010. |
| `@needs:` | section[] | Selective loading from `extends:` schemas. Omit to load everything. |
| `agents:` | obj | Model bindings for executor and orchestrator roles. |
| `mode:` | enum | `production` \| `development` \| `debug` \| `dry_run` |

### `@needs:` — Selective Extension Loading

Declares which sections of an `extends:` schema to load. Reduces schema context per execution.

```nodus
;; flat form — single extension
@needs: [§commands_sdd, §macros_sdd, §types_sdd]

;; keyed form — multiple extensions
@needs: {
  "sdd.schema.nodus":  [§commands_sdd, §macros_sdd],
  "chat.schema.nodus": [§commands_chat]
}
```

- Omit `@needs:` to load the full extension schema (backward-compatible default).
- `§meta` and all `!!rules` of every extension are **always** loaded regardless.
- Unknown section → `NODUS:SCHEMA_MISMATCH` warning, loading continues.

### Context File Loading `@ctx:`

Loads static context documents into `$ctx` before steps execute. Files are resolved from `.nodus/context/`.

```nodus
@ctx: [brand_voice, tone_guidelines, mention_rules]
```

At runtime `$ctx.brand_voice`, `$ctx.tone_guidelines`, etc. are available as variables.

A named context entry can also reference a path explicitly in `config.json`:

```json
"context": {
  "brand_voice": ".nodus/context/brand_voice.md",
  "mention_rules": ".nodus/context/mention_rules.md"
}
```

### Dynamic Workflow References `wf:name`

Workflows reference each other at runtime using the `wf:<identifier>` ref type.
The identifier must match a `§wf:` declaration (and therefore a filename) without the `.nodus` extension.

```nodus
;; In @ON triggers
@ON: new_mention → RUN(wf:beautiful_mention)
@ON: sentiment < 0.2 → RUN(wf:crisis_response)

;; In @steps — hand off and stop
ROUTE(wf:support_triage) !BREAK

;; In @steps — call and continue
EXECUTE(wf:enrich_user) → $enriched
```

| Command | Returns | Description |
| :--- | :--- | :--- |
| `ROUTE(wf:name)` | void | Hand off execution. Typically followed by `!BREAK`. |
| `EXECUTE(wf:name)` | NODUS:RESULT | Call a workflow and receive its full result object. |
| `SIMULATE(wf:name)` | NODUS:RESULT | Dry-run a workflow without side effects. |

Workflow names are resolved via `"workflows": { "root": "./workflows" }` in `config.json`.

### Dynamic Macro References `@macro:name`

Macros are reusable command chains. They can be defined inline in a workflow or in a schema file.

```nodus
;; Define
@macro:COMPOSE_REPLY
  1. TONE($pref.tone)
  2. GEN(reply) +ctx=$meta +max_len=280 → $draft
  3. VALIDATE($draft) ^brand_voice ^len:280 → $validated
@end

;; Call
RUN(@macro:COMPOSE_REPLY) +pref=$user.pref → $validated
```

Macros defined in `extends:` schema files are available to all workflows in the project.

### Resolution Order Summary

```
§runtime.core         →  loaded first, base vocabulary
§runtime.extends[]    →  loaded in order, extend vocabulary
config.nodus          →  global !! rules and constants
@ctx: [...]           →  loaded before @steps, scoped to workflow
wf:name / @macro:name →  resolved at runtime during step execution
```

## 6. Modifiers & Attributes

### `+param=val` — Step Modifiers

Named arguments passed to a command.

```nodus
GEN(reply) +tone=warm +max_len=280
FETCH($url) +timeout=10 +retries=3
```

### `^rule` — Validators

Hard assertions checked by `VALIDATE()`.

```nodus
VALIDATE($out) ^no_pii ^len:280 ^brand_voice
```

### `~flag` — Analysis Extractors

Specific dimensions to extract during `ANALYZE()`.

```nodus
ANALYZE($raw) ~sentiment ~urgency ~entities
```

## 7. Symbol Quick Reference

| Symbol | Role | Analogy |
| :--- | :--- | :--- |
| `§` | Section / block declaration | namespace |
| `§runtime:` | Environment block (schema, agents, mode) | venv activate |
| `@ON:` | Event trigger | event listener |
| `@in:` `@out:` | I/O contract | function signature |
| `@ctx:` | Context file loader | import |
| `@err:` | Error handler | catch |
| `@test:` | Inline test block | unit test |
| `@macro:` | Reusable command chain definition | function def |
| `@needs:` | Selective extension section loading | selective import |
| `!!` | Absolute rule — inviolable | hard constraint |
| `!PREF:` | Soft preference — default behavior | weight / default |
| `!BREAK` | Controlled exit — status=ABORTED | break |
| `!SKIP` | Skip current loop iteration | continue |
| `!HALT` | Fatal stop — status=FAILED; requires ESCALATE() | panic |
| `!PAUSE` | Suspend workflow — status=PAUSED; human re-trigger only | suspend |
| `$` | Variable | variable |
| `$CFG.*` | Global project constant (from config.nodus) | const |
| `→` | Pipeline / assignment | pipe / = |
| `?.` | Optional chaining — null-safe path access | `?.` (JS/Kotlin) |
| `?IF` `?ELIF` `?ELSE` | Conditionals | if / else |
| `?SWITCH` | Multi-branch dispatch on a scalar value | switch / match |
| `WHERE` | Inline collection filter (implicit `$it`) | `.filter()` |
| `FIRST` `LAST` | First / last item, optional `WHERE` filter | `.first()` |
| `~FOR` | Loop over collection | for loop |
| `~UNTIL` | Loop until condition (requires `MAX:n`) | while loop |
| `~MAP` | Single-line collection transform (implicit `$it`) | `.map()` |
| `~RETRY:n` | Step-level retry on failure | retry decorator |
| `~PARALLEL` `~JOIN` | Concurrent branches | async / await |
| `~END` | Close a block | `}` |
| `+param=val` | Named argument modifier | kwarg |
| `^rule` | Validation constraint | assert |
| `~flag` | Analysis extractor | flag |
| `"$var"` | String interpolation in literals | f-string |
| `wf:name` | Workflow reference (`ROUTE` / `EXECUTE` / `@ON`) | module ref |
| `@macro:name` | Macro call reference (`RUN`) | function call |
| `;` `;;` | Comment | `//` |
