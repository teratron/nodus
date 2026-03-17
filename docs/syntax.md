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
  agents:  { executor: claude-sonnet-4 }
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

Supports operators: `<`, `>`, `=`, `!=`, `CONTAINS`, `IN`, `NOT`.

```nodus
?IF $sentiment < 0 → TONE(empathetic)
?ELIF $sentiment < 0.5 → TONE(neutral)
?ELSE → TONE(warm)
```

### `!BREAK` / `!SKIP` — Execution Control

- `!BREAK` — stop execution of the current workflow immediately.
- `!SKIP` — skip the current loop iteration and continue.

```nodus
?IF $meta.sentiment < 0.2 → ROUTE(wf:crisis) !BREAK
~FOR $item IN $list:
    ?IF $item.skip = true → !SKIP
    PROCESS($item) → $result
~END
```

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

### `~PARALLEL / ~JOIN` — Concurrency

Executes branches concurrently. `~JOIN` collects all outputs into a single object.

```nodus
~PARALLEL:
    ANALYZE($text) ~sentiment → $s
    ANALYZE($text) ~intent    → $i
    ANALYZE($text) ~entities  → $e
~JOIN → $meta
```

## 4. Variables & Constants

### `$` — Variables

Variables are assigned via `→` and scoped to the workflow. See [schema.md](schema.md) for reserved variables.

```nodus
$raw, $meta, $out, $error, $draft
```

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
  core:    .nodus/core/schema.nodus          ;; required — base vocabulary
  extends: [
    .nodus/schema/brand_voice.nodus          ;; project schema extensions
    .nodus/extensions/nodus-social@1.0/schema.nodus  ;; installed pack schema
  ]
  agents:  { executor: claude-sonnet-4 }
  mode:    production
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `core:` | path | Path to `schema.nodus`. Must resolve or execution halts (E011). |
| `extends:` | path[] | Additional schema files loaded in order. Missing files raise W011. |
| `agents:` | obj | Model bindings for executor and orchestrator roles. |
| `mode:` | enum | `production` \| `development` \| `debug` \| `dry_run` |

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
| `!!` | Absolute rule — inviolable | hard constraint |
| `!PREF:` | Soft preference — default behavior | weight / default |
| `!BREAK` | Stop current workflow | break |
| `!SKIP` | Skip current loop iteration | continue |
| `$` | Variable | variable |
| `$CFG.*` | Global project constant (from config.nodus) | const |
| `→` | Pipeline / assignment | pipe / = |
| `?IF` `?ELIF` `?ELSE` | Conditionals | if / else |
| `~FOR` | Loop over collection | for loop |
| `~UNTIL` | Loop until condition (requires `MAX:n`) | while loop |
| `~PARALLEL` `~JOIN` | Concurrent branches | async / await |
| `~END` | Close a block | `}` |
| `+param=val` | Named argument modifier | kwarg |
| `^rule` | Validation constraint | assert |
| `~flag` | Analysis extractor | flag |
| `wf:name` | Workflow reference (`ROUTE` / `EXECUTE` / `@ON`) | module ref |
| `@macro:name` | Macro call reference (`RUN`) | function call |
| `;` `;;` | Comment | `//` |
