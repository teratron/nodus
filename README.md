# NODUS

> **N**ode **O**rchestration **D**SL for **U**nified **S**ystems

A compact, symbolic language designed for LLM-to-LLM communication in multi-agent pipelines.  
Written by an orchestrator AI. Interpreted by an executor AI. Understood by humans.

## What is NODUS?

Modern AI workflows involve multiple agents passing instructions to each other. The problem: natural language is verbose, ambiguous, and burns tokens. Code is too rigid and loses semantic meaning.

**NODUS is the middle ground** — a symbolic DSL that is:

- ✅ Compact (10x token reduction vs plain text)
- ✅ Unambiguous (no interpretation drift)
- ✅ Human-readable (dual-mode rendering)
- ✅ LLM-native (designed for how models actually process context)

## Core Philosophy

> *Enough formal to be unambiguous. Enough semantic to preserve intent.*

NODUS has three layers:

```
[schema.nodus]     →  vocabulary, keywords, rules, triggers
[workflow.nodus]   →  the actual workflow written in NODUS
[executor LLM]     →  interprets workflow through schema, executes
```

## Syntax Overview

### File Header

Every NODUS file starts with a section declaration and a runtime block:

```
§wf:<workflow_name> v<version>

§runtime: {
  core:    ../../core/schema.nodus
  extends: [./schema/schema.nodus]
  agents:  { executor: claude-sonnet-4, orchestrator: claude-opus-4 }
  mode:    production
}
```

The `§runtime:` block is always second — resolved before rules, before steps.  
It tells the agent where to load its vocabulary and who is executing.

### Triggers `@ON:`

Triggers define **when** a workflow activates. They are always declared at the top.

```
@ON: new_mention              → RUN(wf:beautiful_mention)
@ON: sentiment < 0.2          → RUN(wf:crisis)
@ON: schedule:09:00           → RUN(wf:morning_digest)
@ON: webhook:payment_done     → RUN(wf:confirm_order)
@ON: $user.msg CONTAINS "refund" → RUN(wf:support)
```

### Absolute Rules `!!`

Hard constraints that **cannot be violated** under any circumstance.  
Always declared before workflow steps. LLM treats these as base-layer filters.

```
!!NEVER: publish WITHOUT validate
!!ALWAYS: log($out)
!!NEVER: ROUTE(external) IF $data.type = confidential
!!ALWAYS: ESCALATE(human) IF $error.level = critical
```

### Priority Preferences `!PREF:`

Soft rules — important defaults with contextual flexibility.

```
!PREF: tone = brand_voice OVER tone = user_request
!PREF: brevity OVER completeness IF channel = twitter
!PREF: formal OVER casual IF $user.tier = enterprise
```

### Input / Output `@in:` `@out:`

```
@in:  {post_url, tone?=neutral, lang?=auto}
@ctx: [brand_voice, mention_rules]
@out: $result
@err: ESCALATE(human)
```

`?=` denotes optional parameters with default values.  
`@ctx` defines context files/rules to load.

### Variables `$`

```
$raw       →  raw fetched content
$meta      →  analyzed metadata
$draft     →  generated draft
$out       →  final output
$error     →  error object
```

Variables are declared implicitly on first assignment via `→`.

### Pipeline Operator `→`

Passes output of one step as input to the next:

```
FETCH($url) → $raw
ANALYZE($raw) ~sentiment ~intent → $meta
GEN(reply) +ctx=$meta +tone=$tone → $draft
```

### Conditionals `?IF`

```
?IF $meta.sentiment < 0.2  → ROUTE(wf:crisis)  !BREAK
?ELIF $meta.sentiment < 0.5 → TONE(neutral)
?ELSE                        → TONE(warm)
```

`!BREAK` stops execution of the current workflow after routing.  
`!SKIP` skips current iteration without stopping.

### Loops `~FOR` `~UNTIL`

**Iterating over a collection:**

```
~FOR $item IN $mentions:
    PROCESS($item) → $result
    APPEND($result → $out)
~END
```

**Repeat until condition:**

```
~UNTIL $quality > 0.85 | MAX:3:
    REFINE($draft) → $draft
~END
```

`MAX:n` sets a hard iteration limit to prevent infinite loops.

### Parallel Execution `~PARALLEL`

```
~PARALLEL:
    ANALYZE($text) ~sentiment  → $s
    ANALYZE($text) ~intent     → $i
    ANALYZE($text) ~entities   → $e
~JOIN → $meta
```

`~JOIN` collects all parallel outputs into a single object.

### Built-in Commands

| Command | Description |
| --- | --- |
| `FETCH(url)` | Retrieve external content |
| `ANALYZE(input) ~flag` | Run analysis with modifiers |
| `GEN(type) +param=val` | Generate content |
| `VALIDATE(input) ^rule` | Check against a rule |
| `ROUTE(workflow)` | Hand off to another workflow |
| `APPEND(value → list)` | Add to a collection |
| `REFINE(input)` | Improve/iterate on content |
| `ESCALATE(target)` | Send to human or supervisor agent |
| `LOG(value)` | Record to audit trail |
| `TONE(value)` | Set response tone |
| `QUERY_KB(query)` | Semantic search over knowledge base |
| `REMEMBER(key, value)` | Store to long-term memory |
| `RECALL(key)` | Retrieve from long-term memory |
| `RUN(@macro:name)` | Execute a reusable macro |

## Dual-Mode Rendering

NODUS supports two representations of the same workflow.

### NODUS Mode (machine-optimized)

```
§wf:beautiful_mention v1.0
§runtime: { core: ../../core/schema.nodus, mode: production }
@ON: new_mention → RUN(wf:beautiful_mention)
@in: {post_url, tone?=neutral, lang?=auto}
@ctx: [brand_voice, mention_rules]
!!NEVER: publish WITHOUT validate
!PREF: tone = brand_voice OVER tone = $in.tone

@steps:
  1. FETCH($post_url) → $raw
  2. ANALYZE($raw) ~sentiment ~intent → $meta
  3. ?IF $meta.sentiment < 0.2 → ROUTE(wf:crisis) !BREAK
  4. GEN(mention_reply) +tone=$tone +ctx=$meta → $draft
  5. VALIDATE($draft) ^brand_voice ^len:280 → $validated
  6. LOG($validated)
@out: $validated
@err: ESCALATE(human)
```

### HUMAN Mode (same workflow, readable)

```
WORKFLOW: beautiful_mention
TRIGGER: when a new mention is received

INPUT: post URL, tone (default: neutral), language (default: auto)
CONTEXT: load brand voice rules and mention guidelines

RULES:
  - NEVER publish without validation
  - Prefer brand voice over user-requested tone

STEPS:
  1. Fetch the post from URL
  2. Analyze for sentiment and intent
  3. IF sentiment is very negative → escalate to crisis workflow, STOP
  4. Generate a mention reply using tone and context
  5. Validate against brand voice and 280 character limit
  6. Log the result

OUTPUT: validated reply
ON ERROR: escalate to human
```

Both representations are valid NODUS. The schema defines how to parse each.

## Project File Structure

NODUS is designed to be a **non-intrusive tool** — it fits into any existing project without cluttering the root. All NODUS infrastructure lives in a single hidden folder.

```
my-project/               ← any existing project (app, SDD, agent system)
│
├── .nodus/               ← all NODUS infrastructure in one place
│   ├── core/             ← language core, downloaded on nodus init (don't edit)
│   │   ├── schema.nodus
│   │   └── AGENTS.md
│   ├── extensions/       ← installed packs via nodus install (don't edit)
│   │   └── nodus-social@1.0/
│   ├── schema/           ← your schema extensions
│   │   ├── brand_voice.nodus
│   │   └── validators.nodus
│   ├── context/          ← static context files loaded via @ctx
│   │   ├── brand_voice.md
│   │   └── tone_guidelines.md
│   ├── config.nodus      ← business logic: global rules, triggers, constants
│   ├── config.json       ← infrastructure: API keys, models, webhooks
│   └── .cache/           ← validation cache + lock file (gitignore)
│       └── nodus.lock
│
└── workflows/            ← your workflows — name and location is up to you
    ├── social/
    │   ├── beautiful_mention.nodus
    │   └── crisis_response.nodus
    └── support/
        └── ticket_triage.nodus
```

The `workflows/` folder is just a convention. In practice it can be anywhere and named anything — `agents/`, `prompts/`, `ai/`, nested inside `src/`. NODUS finds workflows via `config.json`, not by folder name.

### Two configs — two responsibilities

NODUS intentionally separates business logic from infrastructure:

**`.nodus/config.nodus`** — answers **WHAT** the project does.  
Written in NODUS, read by the **agent**.

```
!!NEVER: publish WITHOUT validate   ← global rules for all workflows
@ON: new_mention → RUN(wf:...)      ← which events trigger what
$CFG.CRISIS_THR = -0.5              ← shared constants
```

**`.nodus/config.json`** — answers **WHERE** the project runs.  
Written in JSON, read by the **CLI and runtime**.

```json
"agents":   { "executor": { "model": "claude-sonnet-4" } }
"channels": { "slack": { "webhook": "env:SLACK_WEBHOOK" } }
"workflows": { "root": "./workflows" }
```

### Agent boot sequence

```
1. .nodus/config.json    → resolve environment, models, API keys
2. .nodus/config.nodus   → load global rules, triggers, constants
3. workflow.nodus        → execute the specific workflow
```

### What to commit

```gitignore
# .gitignore
.nodus/core/          # downloaded on nodus init
.nodus/extensions/    # installed on nodus install
.nodus/.cache/        # generated at runtime
```

Everything else in `.nodus/` is yours — commit it:

```
.nodus/schema/        ✅ your schema extensions
.nodus/context/       ✅ your context files
.nodus/config.nodus   ✅ your rules and triggers
.nodus/config.json    ✅ without secrets (use env: vars)
workflows/            ✅ your workflows
```

## Symbol Reference

| Symbol | Role | Analogy |
| --- | --- | --- |
| `§` | Section/file declaration | namespace |
| `§runtime:` | Environment block | venv activate |
| `@ON:` | Event trigger | event listener |
| `@in:` `@out:` | I/O declaration | function signature |
| `@ctx:` | Context loader | import |
| `@test:` | Inline test block | unit test |
| `@macro:` | Reusable command chain | function |
| `!!` | Absolute rule (hard constraint) | hard limit |
| `!PREF:` | Priority preference (soft rule) | weight/default |
| `!BREAK` | Stop execution | break |
| `!SKIP` | Skip iteration | continue |
| `$` | Variable | variable |
| `$CFG.*` | Global project constant | const |
| `→` | Pipeline / assignment | pipe / = |
| `?IF` `?ELIF` `?ELSE` | Conditionals | if/else |
| `~FOR` | Loop over collection | for loop |
| `~UNTIL` | Loop until condition | while loop |
| `~PARALLEL` `~JOIN` | Concurrent execution | async/await |
| `~END` | Close a block | } |
| `+param=val` | Named argument modifier | kwarg |
| `^rule` | Validation constraint | assert |
| `~flag` | Analysis modifier | flag |

## Design Principles

1. **LLM-first** — syntax is optimized for how language models parse context, not how humans write code
2. **Token density** — every symbol carries maximum semantic weight
3. **Absolute clarity** — `!!` rules are always declared first, loaded as base-layer constraints
4. **Dual-mode** — NODUS mode for machines, HUMAN mode for review and debugging
5. **Schema portability** — one schema file makes any workflow portable across agents and projects
6. **Two-layer config** — business logic (`config.nodus`) stays separate from infrastructure (`nodus.config.json`)

## Quick Start

```bash
# Install
pip install nodus-lang

# Initialize a project
nodus init

# Create a workflow
nodus new workflow social/my_workflow

# Validate
nodus validate workflows/social/my_workflow.nodus

# Run
nodus run workflows/social/my_workflow.nodus

# Transpile to HUMAN mode
nodus transpile workflows/social/my_workflow.nodus --to=human

# Run tests
nodus test
```

## Status

🟢 **v0.3.5** — Runtime implemented, CLI available

The Python runtime (lexer, parser, validator, executor, transpiler) and CLI are fully implemented.
This is an evolving specification. Contributions, feedback, and discussion welcome.

## Roadmap

- [x] v0.1 — Core syntax spec
- [x] v0.2 — Schema format + macro system + memory commands
- [x] v0.3 — Lint rules (28 rules across error/warn/info)
- [x] v0.4 — Reference interpreter (Python): lexer, parser, validator, executor, transpiler, CLI
- [ ] v0.5 — VS Code syntax highlighting + standalone binary (brew/winget)
- [ ] v0.6 — npm package + JS runtime shim
- [ ] v1.0 — Stable spec + real-world workflow library

## Origin

NODUS was conceived from hands-on work with multi-agent AI systems, where the need for a compact, unambiguous, and portable instruction language became clear. It bridges the gap between human intent and machine execution.

---

*NODUS — connecting agents, one node at a time.*
