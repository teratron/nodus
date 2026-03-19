# NODUS Core Schema

The schema (`packages/spec/core/schema.nodus`) is the vocabulary contract for all workflows.
It defines the grammar, commands, types, and constraints that an agent can understand.

## 1. Constitutional Rules (`!!`)

Fundamental constraints that apply to all agents and interactions:

- **Always** return a structured `NODUS:RESULT`.
- **Never** execute steps before loading schema and `!!` rules.
- **Never** bypass a `!!` rule, even if requested by an orchestrator.
- **Always** respect `MAX:n` limits in loops.
- **Never** modify `$out` after `LOG($out)`.

## 2. Core Commands

### Data Commands

| Command | Example | Description |
| :--- | :--- | :--- |
| `FETCH(target)` | `FETCH($url) +timeout=10 → $raw` | Retrieve external content. |
| `STORE(key, value)` | `STORE("cache_key", $result)` | Persist data to storage. |
| `LOAD(key)` | `LOAD("cache_key") → $data` | Load persisted data. |
| `APPEND(value → list)` | `APPEND($item → $results)` | Add to a collection. |
| `MERGE(a, b)` | `MERGE($ctx, $meta) → $combined` | Merge two objects. |

### Analysis Commands

| Command | Example | Description |
| :--- | :--- | :--- |
| `ANALYZE(input)` | `ANALYZE($text) ~sentiment ~intent → $meta` | Run NLP analysis with flags. |
| `SCORE(input)` | `SCORE($draft) → $quality` | Score quality (0.0–1.0). |
| `COMPARE(a, b)` | `COMPARE($draft, $reference) → $diff` | Compare two values. |

### Generation Commands

| Command | Example | Description |
| :--- | :--- | :--- |
| `GEN(type)` | `GEN(reply) +tone=warm +max_len=280 → $draft` | Generate content. |
| `REFINE(input)` | `REFINE($draft) +focus=clarity → $draft` | Improve existing content. |
| `TRANSLATE(input)` | `TRANSLATE($text) +lang=en → $translated` | Translate text. |
| `SUMMARIZE(input)` | `SUMMARIZE($doc) +max_len=100 → $summary` | Summarize content. |

### Validation & Routing

| Command | Example | Description |
| :--- | :--- | :--- |
| `VALIDATE(input)` | `VALIDATE($out) ^no_pii ^len:500 → $ok` | Check against rules. |
| `ROUTE(wf)` | `ROUTE(wf:support) !BREAK` | Hand off to another workflow. |
| `ESCALATE(target)` | `ESCALATE(human) +msg="Critical Error"` | Alert a human or supervisor agent. |
| `PUBLISH(output)` | `PUBLISH($validated)` | Publish final output (requires prior VALIDATE). |
| `NOTIFY(target)` | `NOTIFY(slack) +msg=$summary` | Send a notification. |

### Memory Commands

| Command | Example | Description |
| :--- | :--- | :--- |
| `QUERY_KB(query)` | `QUERY_KB($in.question) → $kb_results` | Semantic search over knowledge base. |
| `REMEMBER(key, value)` | `REMEMBER("user_pref", $pref)` | Store to long-term memory. |
| `RECALL(key)` | `RECALL("user_pref") → $pref` | Retrieve from long-term memory. |
| `FORGET(key)` | `FORGET("stale_data")` | Delete from long-term memory. |

### Logging & Control

| Command | Example | Description |
| :--- | :--- | :--- |
| `LOG(value)` | `LOG($out)` | Commit to audit trail (locks `$out`). |
| `TONE(value)` | `TONE(warm)` | Set the response tone for subsequent steps. |
| `WAIT(duration)` | `WAIT(5) +unit=s` | Pause execution. unit: ms \| s \| min. |
| `DEBUG(value)` | `DEBUG($meta)` | Output debug info (non-production only). |
| `COUNTER(key)` | `COUNTER("hits") +increment=1 → $n` | Increment a named counter; returns new value. |

### File System Commands

| Command | Example | Description |
| :--- | :--- | :--- |
| `READ_FILE(path)` | `READ_FILE(".design/INDEX.md") → $content` | Read a local file; returns null if absent. |
| `SCAN_DIR(path)` | `SCAN_DIR(".") +depth=2 → $files` | List files/dirs; returns `{name, path, type, size}[]`. |
| `ENV(key)` | `ENV("API_KEY") → $key` | Read an environment variable; returns null if unset. |
| `DATE(format?)` | `DATE("YYYY-MM-DD") → $today` | Current date/time. Default: ISO 8601. |
| `GIT(subcommand)` | `GIT("log") +args=["--oneline","-10"] → $log` | Read-only git query (log/status/diff/show). |

### Human Interaction Commands

| Command | Example | Description |
| :--- | :--- | :--- |
| `ASK(prompt)` | `ASK("Proceed?") +type=confirm → $ok` | Block and ask the human a question. Resumes on answer. |
| `CONFIRM(content)` | `CONFIRM($plan) +msg="Review:" → $ok` | Present content and request approval decision. |

`ASK` types: `str` \| `bool` \| `confirm` \| `choice` \| `multi_choice`.
`CONFIRM` returns `bool` by default; returns the chosen label string when `+actions` is set.

## 3. Reserved Variables

| Variable | Description |
| :--- | :--- |
| `$in` | Input payload (from `@in:`). |
| `$out` | Final workflow output. |
| `$error` | Error context object. |
| `$meta` | Analysis results. |
| `$raw` | Raw fetched content. |
| `$draft` | Generated draft (pre-validation). |
| `$ctx` | Context data loaded via `@ctx:`. |
| `$user` | User session data. |
| `$session` | Session metadata. |
| `$log` | Execution log accumulator. |
| `$flags` | Execution flags. |
| `$quality` | Current quality score (0.0–1.0). |
| `$sentiment` | Sentiment score (-1.0 to 1.0). |
| `$confidence` | Confidence score (0.0–1.0). |
| `$memory` | Long-term memory object. |
| `$kb_results` | Knowledge base query results. |

## 4. Analysis Flags (`~`)

Flags for the `ANALYZE()` command:

| Flag | Output | Description |
| :--- | :--- | :--- |
| `~sentiment` | -1.0 to 1.0 | Positive/negative polarity. |
| `~intent` | str | Detected purpose (question, complaint, spam, …). |
| `~toxicity` | 0.0 to 1.0 | Harmful content score. |
| `~urgency` | 0.0 to 1.0 | Time-criticality score. |
| `~entities` | list | Named entity extraction. |
| `~lang` | str | Detected language code. |
| `~pii` | bool | Detects sensitive personal data. |

## 5. Validators (`^`)

Rules for the `VALIDATE()` command:

| Rule | Description |
| :--- | :--- |
| `^brand_voice` | Matches project branding guidelines. |
| `^len:n` | Maximum character/token limit. |
| `^no_pii` | Blocks personally identifiable information. |
| `^no_toxic` | Blocks toxic or harmful content. |
| `^approved` | Whitelist check against approved content. |

## 6. Tone Registry

Valid values for `TONE()`, `GEN() +tone=`, and `!PREF: tone =`:

`warm`, `neutral`, `formal`, `casual`, `urgent`, `empathetic`, `brand`

## 6. Operators

### Condition Operators

`=` `!=` `<` `>` `<=` `>=` `CONTAINS` `IN` `NOT` `AND` `OR`

### `MATCHES` — Regex

```nodus
$in.arg MATCHES "^T-[A-Z0-9]+"   ;; → true | false
$path   MATCHES "(?i)\\.(md|nodus)$"
```

Evaluated deterministically by the runtime — not via LLM. PCRE syntax. Use `(?i)` prefix for case-insensitive.

### `?.` — Optional Chaining

Short-circuits to `null` if any segment is null. Does not trigger `NODUS:UNDEFINED_VAR`.

```nodus
$user?.preferences?.theme
ANALYZE($ws_config?.workspaces) → $scope
```

### `WHERE / FIRST / LAST` — Collection Expressions

```nodus
$items WHERE $it.active = true          → $active
FIRST($log WHERE $it.level = "error")  → $first_error
LAST($collection)                       → $tail
```

`$it` is the implicit iteration variable inside `WHERE` conditions.

## 7. Error Codes

| Code | Category | Trigger |
| :--- | :--- | :--- |
| `NODUS:RULE_VIOLATION` | runtime | A `!!` absolute rule was violated. |
| `NODUS:RULE_CONFLICT` | runtime | Two `!!` rules contradict each other. |
| `NODUS:PARSE_ERROR` | parse | Workflow file failed to parse. |
| `NODUS:NO_SCHEMA` | parse | `schema.nodus` not found — base mode. |
| `NODUS:SCHEMA_MISMATCH` | parse | Schema version ≠ workflow version. |
| `NODUS:NO_TRIGGER` | runtime | No `@ON` condition matched the input. |
| `NODUS:UNDEFINED_VAR` | runtime | Referenced `$var` has no value. |
| `NODUS:UNDEFINED_CMD` | runtime | Unknown command encountered. |
| `NODUS:MAX_REACHED` | runtime | `~UNTIL` or `~FOR` hit `MAX:n` limit. |
| `NODUS:ROUTE_NOT_FOUND` | routing | `ROUTE(wf:name)` target does not exist. |
| `NODUS:VALIDATION_FAILED` | validation | `VALIDATE()` returned false. |
| `NODUS:UNHANDLED_ERROR` | runtime | Error with no `@err` handler. |
| `NODUS:SWITCH_NO_MATCH` | control | `?SWITCH` had no matching arm and no `*` wildcard. |
| `NODUS:PAUSED` | control | `!PAUSE` suspended the workflow. |
| `NODUS:COUNTER_OVERFLOW` | runtime | `COUNTER()` reached `+max` limit. |
| `NODUS:DIALOG_TIMEOUT` | dialog | `ASK()` or `CONFIRM()` timed out. |
| `NODUS:DIALOG_REJECTED` | dialog | `CONFIRM()` rejected with `+strict=true`. |
