# Contributing to NODUS

Thank you for your interest in contributing to NODUS.  
This document covers repository structure, naming conventions, and contribution guidelines.

## Repository Structure

```
nodus/
│
├── core/                          ← language primitives (maintainers only)
│   └── schema.nodus               ← core vocabulary, commands, types
│
├── workflows/                     ← example and reference workflows
│   ├── social/
│   │   ├── beautiful_mention.nodus
│   │   └── crisis_response.nodus
│   ├── support/
│   │   └── ticket_triage.nodus
│   └── _shared/                   ← reusable sub-workflows
│
├── schema/                        ← project-level schema extensions
│   ├── brand_voice.nodus
│   └── validators.nodus
│
├── context/                       ← static context files loaded via @ctx
│   ├── brand_voice.md
│   └── tone_guidelines.md
│
├── packs/                         ← installable workflow bundles
│   └── nodus-social/
│       ├── pack.json
│       ├── schema.nodus
│       └── workflows/
│
├── templates/                     ← scaffolding templates
│   ├── workflow.template.nodus
│   └── schema.template.nodus
│
├── tests/
│   └── fixtures/                  ← mock data for @test blocks
│
├── docs/                          ← documentation
│   ├── README.md
│   ├── protocol.md
│   ├── syntax.md
│   ├── schema.md
│   └── cli.md
│
├── config.nodus                   ← global rules, triggers, constants
├── nodus.config.json              ← infrastructure, models, API bindings
├── schema.nodus                   ← core schema (symlink to core/)
├── cli.nodus                      ← CLI meta-workflow
├── AGENTS.md                      ← agent interpretation protocol
├── README.md                      ← language spec and quick start
└── CONTRIBUTING.md                ← this file
```

## What Goes Where

| Content | Location |
| --- | --- |
| New core commands, types, flags | `core/schema.nodus` — maintainers only |
| New built-in macros | `core/schema.nodus` → `§macros` |
| New lint rules | `core/schema.nodus` → `§lint` |
| Example workflows | `workflows/<domain>/` |
| Reusable sub-workflows | `workflows/_shared/` |
| Schema extensions | `schema/` |
| Workflow bundles | `packs/<pack-name>/` |
| Documentation | `docs/` |
| Mock fixtures for tests | `tests/fixtures/` |

## Naming Conventions

### Files

```
workflows/social/beautiful_mention.nodus   ← snake_case, domain subfolder
schema/brand_voice.nodus                   ← snake_case
packs/nodus-social/                        ← kebab-case for pack names
tests/fixtures/positive_tweet.json         ← snake_case
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
§runtime: { ... }      ← schema paths and agent bindings
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

## Running Tests

```bash
nodus test                          # run all @test blocks
nodus test --tag=smoke              # smoke tests only
nodus test workflows/social/        # test a specific folder
nodus validate ./workflows/         # lint all workflows
```

---

*NODUS v0.1* — "Enough formal to be unambiguous. Enough semantic to preserve intent."
