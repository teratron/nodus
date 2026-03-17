# NODUS

> The assembly language for AI Agents. Compact, unambiguous, and LLM-native.

NODUS is a symbolic DSL for LLM-to-LLM communication in multi-agent pipelines.
Written by an orchestrator. Interpreted by an executor. Understood by humans.

## Why NODUS?

Natural language is verbose and ambiguous. Code is rigid and loses semantic meaning.
NODUS is the middle ground — precise enough for machines, readable enough for people.

```
[schema.nodus]   →  vocabulary, commands, rules
[workflow.nodus] →  the actual workflow
[executor LLM]   →  interprets and executes
```

> *Enough formal to be unambiguous. Enough semantic to preserve intent.*

## Example

A workflow that responds to social media mentions:

```nodus
§wf:beautiful_mention v1.0
§runtime: { core: .nodus/core/schema.nodus, mode: production }

@ON: new_mention
@in:  { post_url, tone?=neutral }
@ctx: [brand_voice]
!!NEVER: publish WITHOUT validate
!PREF: tone = brand_voice OVER tone = $in.tone

@steps:
  1. FETCH($post_url)               → $raw
  2. ANALYZE($raw) ~sentiment       → $meta
  3. ?IF $meta.sentiment < 0.2      → ROUTE(wf:crisis) !BREAK
  4. GEN(reply) +tone=$tone         → $draft
  5. VALIDATE($draft) ^brand_voice ^len:280
  6. PUBLISH($draft)
  7. LOG($draft)
@out: $draft
@err: ESCALATE(human)
```

The same workflow in HUMAN mode (`nodus transpile --to=human`):

```
WORKFLOW: beautiful_mention
TRIGGER: when a new mention is received

RULES:
  - NEVER publish without validation
  - Prefer brand voice over user-requested tone

STEPS:
  1. Fetch the post
  2. Analyze sentiment
  3. IF very negative → route to crisis workflow, STOP
  4. Generate reply with tone
  5. Validate against brand voice and 280 char limit
  6. Publish
  7. Log result

ON ERROR: escalate to human
```

Both representations are valid NODUS — same logic, different rendering.

## Install

```bash
pip install nodus-lang
nodus init
```

## Quick Start

```bash
# Scaffold a new workflow from template
nodus new workflow social/my_workflow

# Validate (28 lint rules)
nodus validate workflows/social/my_workflow.nodus

# Run
nodus run workflows/social/my_workflow.nodus

# Convert to human-readable
nodus transpile workflows/social/my_workflow.nodus --to=human

# Run inline tests
nodus test
```

## Features

- **Token-dense** — ~10x more compact than plain-text instructions
- **Unambiguous** — `!!` hard constraints prevent interpretation drift
- **Dual-mode** — same workflow in compact NODUS or readable HUMAN mode
- **Schema-portable** — one `schema.nodus` makes workflows portable across agents
- **LLM-native** — designed for how models parse context, not how humans write code
- **28 lint rules** — `nodus validate` catches errors before runtime
- **Python runtime** — lexer, parser, validator, executor, transpiler included

## Documentation

- [Syntax & Grammar](docs/syntax.md) — symbols, operators, blocks, file references
- [Core Schema](docs/schema.md) — commands, variables, flags, validators
- [Interpretation Protocol](docs/protocol.md) — agent boot sequence and execution rules
- [CLI Reference](docs/cli.md) — all commands, flags, and exit codes
- [Contributing](CONTRIBUTING.md) — project structure, naming conventions, contribution guide

## Status

🟢 **v0.3.6** — Python runtime and CLI implemented. Evolving specification.

## Roadmap

- [x] v0.1–v0.3 — Core spec, schema, 28 lint rules
- [x] v0.4 — Python runtime: lexer, parser, validator, executor, transpiler, CLI
- [ ] v0.5 — VS Code extension + standalone binary (brew / winget)
- [ ] v0.6 — npm package + JS runtime shim
- [ ] v1.0 — Stable spec + real-world workflow library

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome.

## License

MIT
