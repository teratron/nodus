# NODUS Syntax Cheatsheet

Complete symbol reference for the NODUS language.

## Declarations

| Symbol | Name | Usage | Analogy |
| :--- | :--- | :--- | :--- |
| `§wf:name v1.0` | Workflow header | First line of every `.nodus` file | namespace |
| `§runtime: { }` | Environment | Schema paths, agent bindings, mode | venv activate |
| `@ON:` | Trigger | `@ON: event → RUN(wf:name)` | event listener |
| `@in:` | Input contract | `@in: { field: type, opt?: type = default }` | function args |
| `@out:` | Output | `@out: $variable` | return value |
| `@ctx:` | Context loader | `@ctx: [file1, file2]` → `$ctx.file1` | import |
| `@err:` | Error handler | `@err: ESCALATE(human)` | catch |
| `@macro:` | Macro definition | `@macro:name ... @end` | function def |
| `@test:` | Inline test | `@test: name +tag=smoke { input, expected }` | unit test |
| `;` `;;` | Comment | `; inline` / `;; full line` | `//` |

## Constraints

| Symbol | Name | Usage |
| :--- | :--- | :--- |
| `!!NEVER:` | Hard ban | `!!NEVER: publish WITHOUT validate` |
| `!!ALWAYS:` | Hard require | `!!ALWAYS: log($out)` |
| `!PREF:` | Soft default | `!PREF: tone = brand_voice OVER user` |

## Flow Control

| Symbol | Name | Usage | Requires |
| :--- | :--- | :--- | :--- |
| `→` | Pipeline | `FETCH($url) → $raw` | — |
| `?IF` | Conditional | `?IF $x < 0.2 → action` | — |
| `?ELIF` | Else-if | `?ELIF $x < 0.5 → action` | `?IF` |
| `?ELSE` | Else | `?ELSE → action` | `?IF` |
| `!BREAK` | Stop workflow | `ROUTE(wf:crisis) !BREAK` | — |
| `!SKIP` | Skip iteration | `?IF $skip = true → !SKIP` | loop |
| `~FOR` | For loop | `~FOR $item IN $list: ... ~END` | `~END` |
| `~UNTIL` | Until loop | `~UNTIL $q > 0.85 \| MAX:3: ... ~END` | `MAX:n`, `~END` |
| `~PARALLEL` | Concurrent | `~PARALLEL: ... ~JOIN → $result` | `~JOIN` |
| `~END` | Close block | Closes `~FOR`, `~UNTIL` | — |
| `~JOIN` | Collect parallel | Closes `~PARALLEL` | — |

## Variables

| Variable | Description |
| :--- | :--- |
| `$in` | Input payload (from `@in:`) |
| `$out` | Final workflow output |
| `$error` | Error context |
| `$meta` | Analysis results |
| `$raw` | Raw fetched content |
| `$draft` | Generated draft (pre-validation) |
| `$ctx` | Loaded context data |
| `$user` | User session |
| `$session` | Session metadata |
| `$log` | Execution log |
| `$flags` | Execution flags |
| `$quality` | Quality score (0.0–1.0) |
| `$sentiment` | Sentiment (-1.0 to 1.0) |
| `$confidence` | Confidence (0.0–1.0) |
| `$memory` | Long-term memory |
| `$kb_results` | Knowledge base results |
| `$CFG.*` | Project constants from `config.nodus` |

## Step Modifiers

| Prefix | Name | Usage |
| :--- | :--- | :--- |
| `+param=val` | Modifier | `GEN(reply) +tone=warm +max_len=280` |
| `^rule` | Validator | `VALIDATE($out) ^brand_voice ^no_pii ^len:280` |
| `~flag` | Extractor | `ANALYZE($text) ~sentiment ~intent ~entities` |

## Core Commands

### Data

`FETCH(target)`, `STORE(key, value)`, `LOAD(key)`, `APPEND(value → list)`, `MERGE(a, b)`

### Analysis

`ANALYZE(input) ~flags`, `SCORE(input)`, `COMPARE(a, b)`

### Generation

`GEN(type) +modifiers`, `REFINE(input)`, `TRANSLATE(input) +lang=`, `SUMMARIZE(input)`

### Validation & Routing

`VALIDATE(input) ^rules`, `ROUTE(wf:name)`, `ESCALATE(target)`, `PUBLISH(output)`, `NOTIFY(target)`

### Memory

`QUERY_KB(query)`, `REMEMBER(key, value)`, `RECALL(key)`, `FORGET(key)`

### Control

`LOG(value)`, `TONE(value)`, `WAIT(condition)`, `DEBUG(value)`

## Analysis Flags

| Flag | Output | Description |
| :--- | :--- | :--- |
| `~sentiment` | -1.0 to 1.0 | Positive/negative polarity |
| `~intent` | str | Detected purpose |
| `~toxicity` | 0.0 to 1.0 | Harmful content score |
| `~urgency` | 0.0 to 1.0 | Time-criticality |
| `~entities` | list | Named entity extraction |
| `~lang` | str | Detected language code |
| `~pii` | bool | Personal data detected |

## Validators

| Rule | Description |
| :--- | :--- |
| `^brand_voice` | Matches branding guidelines |
| `^len:n` | Max character/token limit |
| `^no_pii` | Blocks personal data |
| `^no_toxic` | Blocks toxic content |
| `^approved` | Whitelist check |

## Tone Registry

Valid values: `warm`, `neutral`, `formal`, `casual`, `urgent`, `empathetic`, `brand`

## Type System

| Type | Example |
| :--- | :--- |
| `str` | `username: str` |
| `int` | `count: int` |
| `float` | `threshold: float` |
| `bool` | `force?: bool = false` |
| `url` | `post_url: url` |
| `list` | `items: list` |
| `obj` | `config: obj` |
| `any` | `payload: any` |

Optional fields use `?` suffix with default: `field?: type = default`
