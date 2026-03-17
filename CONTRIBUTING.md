# Contributing to NODUS

Thank you for your interest in contributing to NODUS.  
This document covers repository structure, naming conventions, and contribution guidelines.

---

## Repository Structure

```
nodus/                             ← github.com/nodus-lang/nodus
│
├── core/                          ← language primitives (maintainers only)
│   ├── schema.nodus               ← core vocabulary, commands, types
│   └── AGENTS.md                  ← agent interpretation protocol
│
├── templates/                     ← scaffolding templates
│   ├── workflow.template.nodus
│   └── schema.template.nodus
│
├── examples/                      ← reference workflows
│   ├── social/
│   │   └── beautiful_mention.nodus
│   └── support/
│       └── ticket_triage.nodus
│
├── packs/                         ← official installable packs
│   └── nodus-social/
│       ├── pack.json
│       ├── schema.nodus
│       └── workflows/
│
├── docs/
│   ├── README.md
│   ├── protocol.md
│   ├── syntax.md
│   ├── schema.md
│   └── cli.md
│
├── cli.nodus                      ← CLI meta-workflow
├── README.md
└── CONTRIBUTING.md
```

---

## User Project Structure

When a user runs `nodus init` in their project, NODUS creates a single hidden folder:

```
my-project/                        ← any existing project
│
├── .nodus/                        ← all NODUS infrastructure
│   ├── core/                      ← language core (nodus init, don't edit)
│   │   ├── schema.nodus
│   │   └── AGENTS.md
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
└── workflows/                     ← user workflows (name and location is flexible)
    ├── social/
    └── support/
```

The `workflows/` folder is a **convention, not a requirement**.  
It can be named and placed anywhere — `agents/`, `prompts/`, `ai/`, inside `src/`.  
NODUS locates workflows via `.nodus/config.json`, not by folder name.

---

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
v<major>.<minor>.<patch>
```

- Increment **minor** for non-breaking changes (`v1.0.0` → `v1.1.0`)
- Increment **major** for breaking changes to `@in` or `@out` contracts (`v1.x.x` → `v2.0.0`)

### Constants in `config.nodus`

```
$CFG.CONSTANT_NAME = value   ← SCREAMING_SNAKE_CASE with $CFG. prefix
```

---

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

---

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

---

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

---

## Contribution Types

| Type | Branch | Notes |
| --- | --- | --- |
| Bug fix in existing workflow | `fix/<name>` | Include failing `@test` that now passes |
| New workflow | `feat/workflow-<name>` | Full checklist required |
| New pack | `feat/pack-<name>` | Include README and example context |
| Core schema change | `core/<description>` | Maintainers review required |
| Documentation | `docs/<page>` | Keep HUMAN MODE sections in sync |

---

## Language Preferences

- All code, comments, variable names, and documentation: **English**
- Commit messages and PR titles: **English**
- Chat discussions and project planning: **Russian**

---

## Running Tests

```bash
nodus test                          # run all @test blocks
nodus test --tag=smoke              # smoke tests only
nodus test workflows/social/        # test a specific folder
nodus validate ./workflows/         # lint all workflows
nodus schema inspect                # print resolved .nodus/schema/
```

---

*NODUS v0.1* — "Enough formal to be unambiguous. Enough semantic to preserve intent."
