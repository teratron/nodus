# NODUS Lint Rules

All 28 validation rules checked by `nodus validate`. Grouped by severity.

## Errors (E) — Block Execution

Validation errors prevent workflow execution. Exit code: `1`.

| Code | Rule | Fix |
| :--- | :--- | :--- |
| E001 | `§runtime:` block is required | Add a `§runtime: { core: ... }` block |
| E002 | `§runtime:` must be the second block | Move `§runtime:` right after `§wf:` header |
| E003 | `!!` rules must appear before `@steps:` | Move all `!!NEVER:` / `!!ALWAYS:` above `@steps:` |
| E004 | Variable used before assignment | Assign `$var` via `→` before referencing it |
| E005 | `PUBLISH` requires prior `VALIDATE` | Add `VALIDATE($draft) ^rules` before `PUBLISH()` |
| E006 | Invalid command name | Check spelling against known commands in `schema.nodus` |
| E007 | Unclosed `~FOR` or `~UNTIL` block | Add matching `~END` |
| E008 | Unclosed `~PARALLEL` block | Add matching `~JOIN` |
| E009 | Invalid `§runtime:` field | Check `core:`, `extends:`, `agents:`, `mode:` fields |
| E010 | `~UNTIL` loop missing `MAX:n` | Add `MAX:n` (e.g. `~UNTIL $q > 0.85 \| MAX:3:`) |
| E011 | Schema file not found | Verify `core:` path in `§runtime:` resolves to a file |
| E012 | Workflow name doesn't match filename | `§wf:my_flow` → file must be `my_flow.nodus` |

## Warnings (W) — Unsafe but Runnable

Warnings indicate risky patterns. Workflow can still run.

| Code | Rule | Fix |
| :--- | :--- | :--- |
| W001 | No `@err:` handler declared | Add `@err: ESCALATE(human)` or custom handler |
| W002 | No `@test:` block present | Add at least one `@test:` block |
| W003 | No HUMAN MODE section | Add `;; HUMAN MODE` comment block describing the workflow |
| W004 | `extends:` schema file not found | Check file path in `§runtime: extends: [...]` |
| W005 | Unused variable declared | Remove or use the `$variable` |
| W006 | Step has no output assignment | Consider adding `→ $var` if the result is needed |
| W007 | `@ctx:` references unknown file | Verify context file exists in `.nodus/context/` |
| W008 | Duplicate `!!` rule | Remove the duplicate constraint |
| W009 | Missing version in `§wf:` header | Add version: `§wf:name v1.0` |
| W010 | Over 20 steps in one workflow | Consider splitting into sub-workflows |
| W011 | Extension schema file missing | Verify `extends:` paths |

## Info (I) — Style Suggestions

Informational hints for best practices. No effect on execution.

| Code | Rule | Fix |
| :--- | :--- | :--- |
| I001 | Consider adding `+timeout` to `FETCH()` | Add `+timeout=10` to prevent hangs |
| I002 | Step modifiers could be more specific | Add explicit `+param=value` modifiers |
| I003 | No `@test:` block tagged `smoke` | Add `+tag=smoke` to at least one test |
| I004 | Long step — consider refactoring | Extract into `@macro:` or sub-workflow |
| I005 | `!PREF:` without matching `!!` rule | Consider whether a hard rule is needed |

## Error Codes (Runtime)

Returned in `NODUS:RESULT.errors` during execution:

| Code | Trigger |
| :--- | :--- |
| `NODUS:RULE_VIOLATION` | A `!!` absolute rule was violated |
| `NODUS:PARSE_ERROR` | Workflow file failed to parse |
| `NODUS:MAX_REACHED` | `~UNTIL` loop hit `MAX:n` limit |
| `NODUS:EXECUTION_FAILED` | A step failed at runtime |
| `NODUS:UNDEFINED_VAR` | Variable referenced before assignment |
| `NODUS:ROUTE_NOT_FOUND` | `ROUTE(wf:name)` target doesn't exist |
| `NODUS:RULE_CONFLICT` | Two `!!` rules contradict each other |
| `NODUS:SCHEMA_MISMATCH` | Schema version doesn't match workflow |
| `NODUS:NO_SCHEMA` | Running without `schema.nodus` |
| `NODUS:NO_TRIGGER` | No `@ON:` trigger matched current input |
| `NODUS:UNHANDLED_ERROR` | Step error with no `@err:` handler |

## Validation Output Format

```
[E001] §runtime: block required but not found       ← blocks execution
[W001] No @err handler declared                     ← warning, still runs
[I003] No @test block tagged 'smoke'                ← suggestion
```

Run validation: `nodus validate <path>`
