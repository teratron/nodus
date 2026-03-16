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

Every NODUS file starts with a section declaration:

```
§wf:<workflow_name> v<version>
```

Example:

```
§wf:beautiful_mention v1.0
```

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

## Dual-Mode Rendering

NODUS supports two representations of the same workflow.

### NODUS Mode (machine-optimized)

```
§wf:beautiful_mention v1.0
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

## File Structure

```
project/
├── schema.nodus          ← vocabulary, rules, keyword definitions
├── workflows/
│   ├── beautiful_mention.nodus
│   ├── crisis.nodus
│   ├── morning_digest.nodus
│   └── support.nodus
└── config.nodus          ← global triggers and constants
```

## Symbol Reference

| Symbol | Role | Analogy |
| --- | --- | --- |
| `§` | Section/file declaration | namespace |
| `@ON:` | Event trigger | event listener |
| `@in:` `@out:` | I/O declaration | function signature |
| `@ctx:` | Context loader | import |
| `!!` | Absolute rule (hard constraint) | hard limit |
| `!PREF:` | Priority preference (soft rule) | weight/default |
| `!BREAK` | Stop execution | break |
| `!SKIP` | Skip iteration | continue |
| `$` | Variable | variable |
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

## Status

🟡 **v0.1 — Draft Specification**

This is an evolving specification. Contributions, feedback, and discussion welcome.

## Roadmap

- [ ] v0.1 — Core syntax spec (this document)
- [ ] v0.2 — Schema format definition
- [ ] v0.3 — Reference interpreter (Python/JS)
- [ ] v0.4 — VS Code syntax highlighting
- [ ] v0.5 — Validation tooling
- [ ] v1.0 — Stable spec + real-world workflow library

## Origin

NODUS was conceived from hands-on work with multi-agent AI systems, where the need for a compact, unambiguous, and portable instruction language became clear. It bridges the gap between human intent and machine execution.

---

*NODUS — connecting agents, one node at a time.*
