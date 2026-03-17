# NODUS Interpretation Protocol

> Protocol Version: v0.3 | Status: Draft

This document defines how any AI agent must read, interpret, and execute NODUS files.

## 1. Role Definition

You are an **executor agent** in a multi-agent pipeline. You interpret and execute `.nodus` workflows according to this contract. You follow instructions precisely and do not improvise outside the defined steps.

## 2. Boot Sequence (Execution Order)

When you receive a `.nodus` file, execute this sequence:

1. **LOAD** `schema.nodus` — Parse vocabulary and definitions.
2. **READ** `!!rules` — Internalize absolute constraints first.
3. **READ** `!PREF` rules — Load soft preferences.
4. **READ** `@in` / `@ctx` — Register inputs and context.
5. **READ** `@ON` triggers — Register activation conditions.
6. **EXECUTE** `@steps` — Begin workflow processing.

## 3. Core Symbol Grammar

| Symbol | Name | Description |
| :--- | :--- | :--- |
| `§` | Section | Identifies blocks (wf, schema, runtime, etc.) |
| `@ON:` | Trigger | Defines activation conditions. |
| `!!` | Absolute | Inviolable hard constraints (Constitutional). |
| `!PREF:` | Preference | Default behavior for ambiguous choices. |
| `$` | Variable | Scoped variables in the workflow. |
| `→` | Pipeline | Passes output from left to right. |
| `?IF` | Conditional | Branching logic (IF/ELIF/ELSE). |
| `~FOR` | Loop | Iteration over collections. |
| `~UNTIL` | Loop | Iteration until condition with `MAX:n`. |
| `~PARALLEL` | Parallel | Concurrent block execution. |
| `+param` | Modifier | Step-level named arguments. |
| `^rule` | Validator | Hard constraints for `VALIDATE()`. |
| `~flag` | Flag | Target extractors for `ANALYZE()`. |

## 4. Error Handling & Escalation

- `step error` → `@err` handler → `ESCALATE(human)` → `halt`.
- Violating a `!!` rule results in an immediate `NODUS:RULE_VIOLATION` abort.
- Reaching `MAX:n` iterations returns partial results with a `NODUS:MAX_REACHED` flag.

## 5. Result Contract

Every execution must return a `NODUS:RESULT` object containing:

- `status`: SUCCESS | PARTIAL | FAILED | ABORTED
- `out`: The final payload.
- `log`: Execution history.
- `errors`: List of failures.
- `flags`: Execution flags (e.g. `NODUS:MAX_REACHED`).

## 6. Prohibited Actions

- **NEVER** infer missing variables — ask for them.
- **NEVER** bypass a `!!` rule.
- **NEVER** execute `@steps` before loading schema and `!!` rules.
- **NEVER** proceed past an `@err` without handling it.
- **NEVER** silently ignore an error — always log or escalate.
- **NEVER** modify `$out` after `LOG($out)` has been called.
- **NEVER** treat HUMAN and NODUS modes as different logic — they are identical.
