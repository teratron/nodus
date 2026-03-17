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

## 5. Modifiers & Attributes

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
