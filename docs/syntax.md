# NODUS Syntax & Grammar

This document provides a detailed breakdown of the NODUS symbolic syntax.

## 1. Declarations

### `§` — Section / Block

Declares a named block or file level metadata.

```nodus
§wf:workflow_name v1.0
§schema:nodus v0.1
```

### `@ON:` — Triggers

Defines activation conditions. Multiple triggers are evaluated top-to-bottom.

```nodus
@ON: new_mention → RUN(wf:beautiful_mention)
```

### `@in:` / `@out:` — Input/Output

Defines the data contract for the workflow. `?=` denotes optional parameters.

```nodus
@in: { username: str, force?: bool = false }
```

## 2. Constraints & Preferences

### `!!` — Absolute Rules

Inviolable hard constraints. If a step violates a `!!` rule, execution stops.

```nodus
!!NEVER: publish WITHOUT prior validation
```

### `!PREF:` — Soft Preferences

Defaults for ambiguous situations. Can be overridden by step modifiers.

```nodus
!PREF: brevity OVER completeness IF channel = twitter
```

## 3. Flow Control

### `→` — Pipeline Operator

The output of the left side becomes the value of the right side (usually a variable assignment).

```nodus
FETCH($url) → $raw
```

### `?IF / ?ELIF / ?ELSE` — Conditionals

Supports standard operators: `<`, `>`, `=`, `!=`, `CONTAINS`, `IN`, `NOT`.

```nodus
?IF $sentiment < 0 → TONE(empathetic)
```

### `~FOR / ~UNTIL` — Loops

Loops must include or allow a `MAX:n` constraint to prevent infinite execution.

```nodus
~UNTIL $quality > 0.8 | MAX:3:
    REFINE($draft) → $draft
~END
```

### `~PARALLEL / ~JOIN` — Concurrency

Executes branches independently and waits for all to finish.

```nodus
~PARALLEL:
    ANALYZE($text) ~sentiment → $s
    ANALYZE($text) ~intent    → $i
~JOIN → $meta
```

## 4. Modifiers & Attributes

### `$` — Variables

Variables are usually locally scoped unless explicitly passed.

```nodus
$raw, $meta, $out, $error
```

### `+param=val` — Step Modifiers

Named arguments for commands.

```nodus
GEN(reply) +tone=warm +max_len=280
```

### `^rule` — Validators

Hard assertions checked by `VALIDATE()`.

```nodus
VALIDATE($out) ^no_pii ^len:280
```

### `~flag` — Extractors

Specific items to extract during `ANALYZE()`.

```nodus
ANALYZE($raw) ~sentiment ~urgency
```
