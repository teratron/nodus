# Contributing to NODUS

Thank you for your interest in contributing to NODUS.  
This document covers repository structure, naming conventions, and contribution guidelines.

## Repository Structure

```
nodus/                             ← github.com/nodus-lang/nodus
│
├── packages/                      ← project core components
│   ├── spec/                      ← LANGUAGE SPECIFICATION (changes slowly)
│   │   ├── core/                  ← language primitives (maintainers only)
│   │   │   ├── schema.nodus
│   │   │   └── ...
│   │   └── ...
│   │
│   ├── runtime/                   ← PYTHON RUNTIME (changes often)
│   │
│   ├── agents/                    ← AI AGENT INTERFACE (canonical source)
│   │   ├── workflows/             ← slash-commands
│   │   │   ├── nodus.*.md
│   │   │   └── ...
│   │   ├── skills/                ← syntax, patterns, lint rules
│   │   │   └── nodus/
│   │   └── rules/                 ← agent behavior rules
│   │
│   └── extensions/                ← IDE support
│
├── installer/                     ← build and packaging scripts
├── packs/                         ← default pack ecosystem
├── demo/                          ← showcase project
├── docs/                          ← documentation
├── examples/                      ← workflow snippets
│
├── .agents/                       ← AI agent skills and workflows (orchestration)
│   ├── skills/
│   │   ├── nodus/                 ← junction → packages/agents/skills/nodus/
│   │   └── ...                    ← generic skills (brainstorming, etc.)
│   └── workflows/
│       ├── nodus.*.md             ← symlinks → packages/agents/workflows/nodus.*.md
│       └── nodus.dev.init.md      ← file: setup symlinks (Windows/Linux)
│
├── .claude/                       ← Claude Desktop specific config
│   ├── commands/                  ← junction → .agents/workflows/
│   ├── skills/                    ← junction → .agents/skills/
│   └── rules/                     ← junction → .agents/rules/
│
├── pyproject.toml                 ← build config and dependencies
├── README.md                      ← quick start
├── CONTRIBUTING.md                ← this file
└── CHANGELOG.md                   ← version history
```

## User Project Structure

When a user runs `nodus init` in their project, NODUS creates a single hidden folder:

```
my-project/                        ← any existing project
│
├── .nodus/                        ← all NODUS infrastructure (created by nodus init)
│   ├── core/                      ← language core (don't edit)
│   │   ├── schema.nodus
│   │   ├── AGENTS.md
│   │   └── cli.nodus
│   ├── extensions/                ← installed packs (nodus install, don't edit)
│   │   └── nodus-social@1.0/
│   ├── schema/                    ← user schema extensions
│   │   ├── brand_voice.nodus
│   │   └── validators.nodus
│   ├── context/                   ← static context files loaded via @ctx
│   │   ├── brand_voice.md
│   │   └── tone_guidelines.md
│   ├── config.json                ← infrastructure: models, API keys, webhooks
│   └── .cache/                    ← generated at runtime (gitignore)
│       └── nodus.lock
│
├── workflows/                     ← user workflows (name and location is flexible)
│   ├── _shared/                   ← reusable sub-workflows
│   ├── social/
│   └── support/
│
├── config.nodus                   ← business logic: rules, triggers, constants
├── logs/                          ← execution logs (NODUS:RESULT objects)
└── tests/                         ← workflow test cases (.test.json)
```

### Workflow folder is a convention, not a requirement

The folder containing user workflows can be **named and placed anywhere** in the project.
NODUS locates workflows via path references in `.nodus/config.json` — not by folder name.

```
"triggers": {
  "new_order": "./automation/orders/confirm.nodus",
  "new_review": "./agents/reply_to_review.nodus",
  "daily_report": "./src/ai/morning_digest.nodus"
}
```

All of these are valid. The user decides the structure; NODUS follows.

### What user workflows are

User workflows are `.nodus` files that the user writes themselves to automate
their own business logic. They are the primary deliverable — everything else
(`.nodus/core/`, `config.json`, schema files) exists to support them.

```
workflows/
├── social/
│   └── reply_to_review.nodus     ← responds to Instagram reviews automatically
├── support/
│   └── ticket_triage.nodus       ← classifies and routes incoming tickets
└── ecommerce/
    └── order_confirm.nodus        ← sends order confirmation emails
```

These files reference the language primitives from `.nodus/core/` but contain
the user's own business rules, tone preferences, and routing logic.

### .agents/ — AI assistant interface (optional)

Projects that use AI coding assistants (Claude, Cursor, Copilot) can add
an `.agents/` folder to give the assistant context about NODUS:

```
my-project/
└── .agents/
    ├── skills/
    │   └── nodus/                 ← junction → packages/agents/skills/nodus/
    │       ├── SKILL.md
    │       └── references/
    └── workflows/
        ├── nodus.run.md           ← link → packages/agents/workflows/nodus.run.md
        ├── nodus.create.md        ← link → packages/agents/workflows/nodus.create.md
        └── nodus.validate.md      ← link → packages/agents/workflows/nodus.validate.md
```

The commands in `.agents/workflows/` are **not wrappers** around user workflows.
They are generic bridges: `/nodus.run` accepts a workflow path as an argument
and runs it. A project-specific command only makes sense when the AI needs to
do something before or after the NODUS runtime — asking the user a question,
checking an external service, or orchestrating multiple steps.

```
.agents/workflows/
├── nodus.run.md          ← generic: "run any workflow"     (always useful)
└── publish_release.md    ← specific: verify changelog →    (project-specific
                               bump version →                orchestration,
                               run workflows/publish.nodus   not just a wrapper)
```

### config.json example (User Project)

```json
{
  "version": "0.1",
  "project": "my-project",
  "schema": {
    "core": ".nodus/core/schema.nodus",
    "extends": ["./.nodus/schema/brand_voice.nodus"]
  },
  "agents": {
    "executor": {
      "model": "claude-sonnet-4",
      "context_files": [".nodus/core/AGENTS.md"]
    }
  },
  "triggers": {
    "new_review":   "./workflows/social/reply_to_review.nodus",
    "new_ticket":   "./workflows/support/ticket_triage.nodus",
    "new_order":    "./workflows/ecommerce/order_confirm.nodus"
  },
  "logging": { "enabled": true, "output": "./logs" }
}
```

## Naming Conventions

### Files

```
workflows/social/reply_to_review.nodus   ← snake_case, domain subfolder
.nodus/schema/brand_voice.nodus          ← snake_case
packs/nodus-social/                      ← kebab-case for pack names
```

### Workflow names

The `§wf:` name must match the filename exactly (enforced by lint rule E012):

```
§wf:reply_to_review v1.0
```

File: `reply_to_review.nodus` ✅  
File: `ReplyToReview.nodus` ❌

### Version format

```
v<major>.<minor>
```

- Increment **minor** for non-breaking changes (`v1.0` → `v1.1`)
- Increment **major** for breaking changes to `@in` or `@out` contracts (`v1.x` → `v2.0`)

### Constants in `config.nodus`

```
$CFG.CONSTANT_NAME = value   ← SCREAMING_SNAKE_CASE with $CFG. prefix
```

## Workflow Checklist

Before submitting a workflow, verify it passes all lint rules:

```bash
nodus validate workflows/your_workflow.nodus
```

Minimum requirements (enforced by linter):

- [ ] `§runtime:` block present and second in file (E001, E002)
- [ ] `!!` rules declared before `@steps` (E003)
- [ ] All `$variables` assigned before use (E004)
- [ ] `PUBLISH` preceded by `VALIDATE` (E005)
- [ ] All `~FOR` / `~UNTIL` closed with `~END` (E007)
- [ ] All `~PARALLEL` closed with `~JOIN` (E008)
- [ ] All `~UNTIL` loops have `MAX:n` (E010)
- [ ] Workflow name matches filename (E012)
- [ ] `@err` handler declared (W001)
- [ ] At least one `@test` block present (W002)
- [ ] HUMAN MODE section present (W003)
- [ ] At least one `@test` tagged `smoke` (I003)

## Writing a New Workflow

```bash
nodus new workflow <domain/name>
```

This scaffolds `workflows/<domain>/<name>.nodus` from `workflow.template.nodus`.

### Required sections (in order)

```
§wf:name v1.0          ← header with version
;; comments            ← Workflow / Purpose / Pack / Author / Updated
§runtime: {
  core:    .nodus/core/schema.nodus
  extends: [.nodus/schema/brand_voice.nodus]
  ...
}                      ← schema paths and agent bindings
@ON: ...               ← triggers
!! rules               ← workflow-level hard constraints
!PREF: rules           ← soft preferences
@in: { ... }           ← input declarations
@ctx: [ ... ]          ← context files
@out: $var             ← output variable
@err: ...              ← error handler
@steps:                ← numbered steps
;; HUMAN MODE          ← plain-language description
@test: ...             ← at least one test block
```

## Writing a Pack

A pack is a shareable bundle of workflows + schema for a specific domain.

### Structure

```
packs/nodus-<domain>/
├── pack.json
├── schema.nodus
├── workflows/
│   └── *.nodus
├── context/
│   └── example_*.md
└── README.md
```

### `pack.json` required fields

```json
{
  "name": "nodus-<domain>",
  "version": "1.0.0",
  "description": "...",
  "author": "your-name",
  "nodus": ">=0.1",
  "workflows": ["workflow_a", "workflow_b"],
  "keywords": ["domain", "tag"]
}
```

## Contribution Types

| Type | Branch | Notes |
| --- | --- | --- |
| Bug fix in existing workflow | `fix/<name>` | Include failing `@test` that now passes |
| New workflow | `feat/workflow-<name>` | Full checklist required |
| New pack | `feat/pack-<name>` | Include README and example context |
| Core schema change | `core/<description>` | Maintainers review required |
| Documentation | `docs/<page>` | Keep HUMAN MODE sections in sync |

## Language Preferences

- All code, comments, variable names, and documentation: **English**
- Commit messages and PR titles: **English**
- Chat discussions and project planning: **Russian**

## Installation Architecture

NODUS is designed to be installed by any type of user — developer, prompt engineer, or non-technical business user. The CLI is the single entry point regardless of how it was installed.

### Runtime architecture

```
┌─────────────────────────────────────────┐
│           nodus CLI (unified interface) │
│         nodus init / run / validate     │
└────────────┬───────────────┬────────────┘
             │               │
    ┌────────▼──────┐ ┌──────▼────────┐
    │  Python core  │ │    JS shim    │
    │  nodus-lang   │ │  nodus-lang   │
    │  (PyPI)       │ │  (npm)        │
    └───────────────┘ └───────────────┘
```

Python is the primary runtime. The npm package is a thin wrapper that calls the Python core under the hood. In packaged releases (brew, winget, standalone), the Python runtime is compiled into a single binary via PyInstaller — no dependency on the user's system Python.

### Installation by audience

**Developer (Python / AI-ML):**

```bash
pip install nodus-lang
nodus init
```

**Developer (Node.js / frontend):**

```bash
npm install -g nodus-lang
nodus init
```

**Prompt engineer / power user:**

```bash
# macOS
brew install nodus-lang

# Linux
curl -fsSL https://nodus-lang.dev/install.sh | sh

# Windows
winget install nodus-lang
```

**Business user / non-technical:**
VS Code extension with an `Initialize NODUS project` button. No terminal required.

### What `nodus init` does

```
nodus init
    │
    ├── 1. detect runtime
    │       python3 available → use Python core
    │       node available    → use JS shim → Python core
    │       neither           → use bundled standalone binary
    │
    ├── 2. create .nodus/
    │       core/             ← downloaded from github releases
    │       extensions/       ← empty, populated by nodus install
    │       schema/           ← empty, user fills in
    │       context/          ← empty, user fills in
    │       .cache/           ← empty, generated at runtime
    │
    ├── 3. scaffold config files
    │       .nodus/config.json ← interactive wizard or defaults
    │       config.nodus       ← base !! rules (at project root)
    │
    ├── 4. update .gitignore
    │       + .nodus/core/
    │       + .nodus/extensions/
    │       + .nodus/.cache/
    │
    └── 5. report
            ✓ NODUS initialized
            ✓ Core schema: .nodus/core/schema.nodus
            Next: nodus new workflow <name>
```

### Release roadmap

| Version | Deliverable | Status |
| --- | --- | --- |
| `v0.1–v0.3` | Core spec, schema, lint rules | ✅ done |
| `v0.4` | Python runtime (interpreter + CLI) | ✅ done |
| `v0.5` | VS Code extension + brew/winget binary | in progress |
| `v0.6` | npm package + JS runtime shim | planned |
| `v1.0` | Stable spec + visual installer + nodus-lang.dev | planned |

## Project Layers

| Layer | Purpose | Primary Actor |
| --- | --- | --- |
| **core** | Language spec, root schema, agent protocol | Maintainers |
| **runtime** | Interpreter, validator, CLI implementation | Developers |
| **user project** | Workflows, brand schema, configs | Prompt Engineers |
| **ecosystem** | Extension, packs, visual tools | Community |

## AI Agent Skill

The repository includes an AI agent skill at `.agents/skills/nodus/` that enables any LLM-powered coding assistant to help users write, validate, and run NODUS workflows. When the skill is loaded into an agent's context, it provides:

- **Guided workflow creation** — scaffolding from templates with correct section order
- **Syntax reference** — complete symbol, command, and type lookup (`references/syntax_cheatsheet.md`)
- **Workflow patterns** — 6 reusable architecture patterns with examples (`references/workflow_patterns.md`)
- **Lint rule index** — all 28 validation rules with fixes (`references/lint_rules.md`)
- **CLI command help** — `init`, `validate`, `run`, `transpile`, `test`
- **Project setup** — step-by-step `nodus init` guidance

### Skill Structure

```
.agents/skills/nodus/
├── SKILL.md                      ← main instructions (UX guide)
└── references/
    ├── syntax_cheatsheet.md      ← all symbols, commands, types
    ├── workflow_patterns.md      ← 6 reusable patterns with code
    └── lint_rules.md             ← E/W/I rules + runtime errors
```

The skill activates automatically when a user asks about NODUS syntax, needs help creating a workflow, encounters a validation error, or wants to set up a new project.

## AI Agent Workflows

The repository provides slash commands in `.agents/workflows/` that guide an AI assistant through complex multi-step tasks. These are not wrappers around user workflows — they are generic operations the assistant performs on behalf of the user.

A project-specific command in `.agents/workflows/` makes sense only when the AI needs to orchestrate something beyond what `nodus run` alone can do: asking the user questions, verifying external state, or combining multiple steps into a single guided flow.

- **`/nodus.compile`** — Full cycle: validation → if clean, transpile to HUMAN mode → result summary.
- **`/nodus.create`** — Interactive wizard: asks for domain, purpose, I/O, and rules → scaffolds the file.
- **`/nodus.explain`** — Analysis: reads workflow → explains trigger, constraints, and steps in plain language.
- **`/nodus.init`** — Setup: runs `nodus init` → guides through configuration of `config.json` and `config.nodus`.
- **`/nodus.pack`** — Packaging: interactive creation of a new pack structure with `pack.json` and schema.
- **`/nodus.run`** — Execution: pre-flight validation → input data preparation → `nodus run` → structured report.
- **`/nodus.test`** — Testing: pre-flight validation → `nodus test` → explains failures and suggests fixes.
- **`/nodus.validate`** — Linting: `nodus validate` → groups issues by severity → provides human-friendly fixes.

## User Personas

- **Prompt Engineer**: Constructs workflows, extends schemas, reviews HUMAN mode.
- **AI Developer**: Integrates NODUS into pipelines, manages agent bindings.
- **Business User**: Installs packs, configures brand voice via visual tools.

## Running Tests

```bash
# Workflow-level tests (@test blocks in .nodus files)
nodus test                          # run all @test blocks
nodus test --tag=smoke              # smoke tests only
nodus test workflows/social/        # test a specific folder

# Lint and schema
nodus validate ./workflows/         # lint all workflows
nodus schema inspect                # print resolved .nodus/schema/

# Python unit tests (runtime development)
uv run pytest                       # run all pytest tests
uv run pytest tests/runtime/test_validator.py  # specific module
```

---

*NODUS v0.4.0* — "Enough formal to be unambiguous. Enough semantic to preserve intent."
