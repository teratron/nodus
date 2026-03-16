# NODUS Core Schema

The schema (`schema.nodus`) is the vocabulary contract for all workflows. It defines the grammar, commands, and types that an agent can understand.

## 1. Constitutional Rules (`!!`)

Fundamental constraints that apply to all interactions:

- **Always** return a structured `NODUS:RESULT`.
- **Never** execute steps before loading rules.
- **Never** bypass a rule, even if requested by an orchestrator.
- **Always** respect `MAX:n` limits in loops.

## 2. Core Commands

| Command | Usage | Result |
| :--- | :--- | :--- |
| `FETCH(target)` | `FETCH($url) +timeout=10 → $raw` | Fetches data from source. |
| `ANALYZE(input)` | `ANALYZE($text) ~sentiment ~intent → $meta` | Runs NLP analysis. |
| `GEN(type)` | `GEN(reply) +tone=warm +max_len=280 → $draft` | Generates content. |
| `VALIDATE(input)` | `VALIDATE($out) ^no_pii ^len:500 → $ok` | Checks against rules. |
| `ROUTE(wf)` | `ROUTE(wf:support) !BREAK` | Hands off to another workflow. |
| `ESCALATE(target)` | `ESCALATE(human) +msg="Critical Error"` | Alerts a human/supervisor. |
| `LOG(value)` | `LOG($out)` | Commits to audit trail (locks value). |

## 3. Data Types & Variables

Fundamental data representations and reserved workflow variables.

### Variables

- `$in`: Input payload.
- `$out`: Final workflow output.
- `$error`: Error context.
- `$meta`: Analysis results.
- `$quality`: Current quality score.
- `$session`: Session metadata.

## 4. Analysis Flags (`~`)

Flags for the `ANALYZE()` command:

- `~sentiment`: -1.0 to 1.0.
- `~intent`: Detects purpose (question, complaint, spam, etc.).
- `~pii`: Detects sensitive personal data.
- `~urgency`: Detects time-criticality.

## 5. Validators (`^`)

Rules for the `VALIDATE()` command:

- `^brand_voice`: Matches project branding.
- `^len:n`: Character limit.
- `^no_pii`: Security check.
- `^approved`: White-list check.

## 6. Tone Registry

Tones for `GEN()` and `TONE()` commands:

`warm`, `neutral`, `formal`, `casual`, `urgent`, `empathetic`, `brand`.
