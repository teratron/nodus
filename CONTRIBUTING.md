# Contributing to NODUS

Thank you for your interest in contributing to NODUS.  
This document covers repository structure, naming conventions, and contribution guidelines.

## Repository Structure

```
nodus/                             ← github.com/nodus-lang/nodus
│
├── packages/
│   ├── spec/                      ← LANGUAGE SPECIFICATION (changes slowly)
│   │   ├── core/                  ← language primitives (maintainers only)
│   │   │   ├── schema.nodus       ← core vocabulary
│   │   │   ├── schema.types.nodus ← extended type definitions
│   │   │   ├── schema.errors.nodus← error code registry
│   │   │   ├── grammar.peg        ← formal PEG grammar
│   │   │   ├── AGENTS.md          ← agent interpretation protocol
│   │   │   └── cli.nodus          ← CLI meta-workflow
│   │   ├── templates/             ← scaffolding templates
│   │   │   ├── workflow.template.nodus
│   │   │   └── schema.template.nodus
│   │   └── VERSION                ← spec version (separate from runtime)
│   │
│   ├── runtime/                   ← PYTHON RUNTIME (changes often)
│   │   ├── interpreter/           ← lexer, parser, AST, validator, executor, transpiler
│   │   ├── cli/                   ← nodus CLI command handlers
│   │   ├── constants.py           ← language-defining constants
│   │   ├── settings.py            ← runtime settings
│   │   └── __init__.py
│   │
│   └── extensions/                ← IDE support
│       ├── vscode/                ← VS Code extension
│       └── jetbrains/             ← JetBrains IDEs (planned)
│
├── examples/                      ← canonical language examples
│   ├── social/
│   │   └── beautiful_mention.nodus
│   └── support/
│       └── ticket_triage.nodus
│
├── packs/                         ← official installable packs
│   └── nodus-social/
│
├── docs/                          ← documentation
│   ├── syntax.md
│   ├── schema.md
│   ├── protocol.md
│   ├── cli.md
│   └── README.md
│
├── tests/                         ← runtime test suite (pytest)
│   └── runtime/
│
├── demo/                          ← sample user project
│   ├── .nodus/
│   │   ├── core/                  ← junction → packages/spec/core/
│   │   ├── schema/                ← user schema extensions
│   │   └── config.json
│   ├── config.nodus               ← business logic config
│   ├── workflows/
│   └── context/
│
├── .agents/                       ← AI agent skills and workflows
│   ├── skills/
│   │   └── nodus/                 ← NODUS workflow assistant skill
│   │       ├── SKILL.md           ← main skill instructions
│   │       └── references/        ← syntax, patterns, lint rules
│   └── workflows/                 ← Slash commands for agents
│       ├── nodus.compile.md       ← validate → transpile → report
│       ├── nodus.create.md        ← interactive workflow creation
│       ├── nodus.explain.md       ← plain-language explanation
│       ├── nodus.init.md          ← guided project setup
│       ├── nodus.pack.md          ← interactive pack creation
│       ├── nodus.run.md           ← pre-flight → execute → report
│       ├── nodus.test.md          ← run @test blocks → report
│       └── nodus.validate.md      ← lint check + auto-fix suggestions
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
├── .nodus/                        ← all NODUS infrastructure
│   ├── core/                      ← language core (nodus init, don't edit)
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
│   ├── config.nodus               ← business logic: rules, triggers, constants
│   ├── config.json                ← infrastructure: models, API keys, webhooks
│   └── .cache/                    ← generated at runtime (gitignore)
│       └── nodus.lock
│
├── workflows/                     ← user workflows (name and location is flexible)
│   ├── _shared/                   ← reusable sub-workflows
│   ├── social/
│   └── support/
│
├── logs/                          ← execution logs (NODUS:RESULT objects)
└── tests/                         ← workflow test cases (.test.json)
```

The `workflows/` folder is a **convention, not a requirement**.  
It can be named and placed anywhere — `agents/`, `prompts/`, `ai/`, inside `src/`.  
NODUS locates workflows via `.nodus/config.json`, not by folder name.

### `config.json` example (User Project)

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
  "logging": { "enabled": true, "output": "./logs" }
}
```

## Naming Conventions

### Files

```
workflows/social/beautiful_mention.nodus   ← snake_case, domain subfolder
.nodus/schema/brand_voice.nodus            ← snake_case
packs/nodus-social/                        ← kebab-case for pack names
```

### Workflow names

The `§wf:` name must match the filename exactly (enforced by lint rule E012):

```
§wf:beautiful_mention v1.0
```

File: `beautiful_mention.nodus` ✅  
File: `BeautifulMention.nodus` ❌

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
    │       config.json       ← interactive wizard or defaults
    │       config.nodus      ← base !! rules
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

The repository provides executable workflows (slash commands) in `.agents/workflows/` that guide an AI assistant through complex multi-step tasks.

- **`/nodus.compile`** — Full cycle: validation → if clean, transpile to HUMAN mode → result summary.
- **`/nodus.create`** — Interactive wizard: asks for domain, purpose, I/O, and rules → scaffolds the file.
- **`/nodus.explain`** — Analysis: reads workflow → explains trigger, constraints, and steps in plain language.
- **`/nodus.init`** — Setup: runs `nodus init` → guides through configuration of `config.json` and `config.nodus`.
- **`/nodus.pack`** — Packaging: interactive creation of a new pack structure with `pack.json` and schema.
- **`/nodus.run`** — Execution: pre-flight validation → input data preparation → `nodus run` → structured report.
- **`/nodus.test`** — Testing: pre-flight validation → `nodus test` → explains failures and suggests fixes.
- **`/nodus.validate`** — Linting: `nodus validate` → groups issues by severity → provides human-friendly fixes.

These workflows use the `// turbo` annotation for performance, allowing the agent to run terminal commands immediately when the step is clear and safe.

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
