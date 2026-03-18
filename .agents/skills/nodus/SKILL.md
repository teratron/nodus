---
name: nodus
description: Guide for writing, validating, and running NODUS workflows. Use this skill when a user wants to create a new workflow, debug syntax errors, understand NODUS symbols, or work with the nodus CLI.
---

# NODUS Workflow Assistant

Help users write, validate, and run NODUS workflows — the symbolic DSL for AI agent pipelines.

## When This Skill Activates

- User wants to **create** a new `.nodus` workflow
- User asks about **NODUS syntax** or symbols (`§`, `!!`, `@ON:`, `→`, etc.)
- User needs help **debugging** a validation error (E001–E012, W001–W003, I001–I003)
- User wants to **run**, **transpile**, or **test** a workflow via CLI
- User wants to **set up** a NODUS project (`nodus init`)
- User wants to **create a pack** (shareable workflow bundle)

## 1. Creating a New Workflow

Follow this sequence:

1. **Ask** the user: what does the workflow do? what triggers it? what are the inputs/outputs?
2. **Scaffold** from the template at `packages/spec/templates/workflow.template.nodus`
3. **Fill in** the sections in required order (see below)
4. **Validate** with `nodus validate <file>`
5. **Test** with `nodus test <file>`

### Required Section Order

Every `.nodus` file must follow this structure, top to bottom:

```nodus
§wf:name v1.0               ;; 1. Header — name matches filename (E012)
;; comments                 ;; 2. Metadata comments
§runtime: { ... }           ;; 3. Runtime — MUST be second block (E001, E002)
@ON: trigger                ;; 4. Triggers
!! rules                    ;; 5. Hard constraints — before @steps (E003)
!PREF: preferences          ;; 6. Soft preferences
@in: { ... }                ;; 7. Input contract
@ctx: [context_files]       ;; 8. Context loader
@out: $variable             ;; 9. Output declaration
@err: handler               ;; 10. Error handler (W001 if missing)
@steps:                     ;; 11. Steps
;; HUMAN MODE               ;; 12. Plain-language description (W003)
@test: test_block           ;; 13. Tests (W002/I003 if missing)
```

### Naming Rules

- Workflow name in `§wf:` **must match** the filename: `§wf:my_flow` → `my_flow.nodus`
- Filenames use `snake_case`
- Pack names use `kebab-case`: `nodus-social`
- Constants use `$CFG.SCREAMING_SNAKE_CASE`

## 2. Symbol Quick Reference

Load `references/syntax_cheatsheet.md` for the full table. Key symbols:

| Symbol | Purpose | Example |
| :--- | :--- | :--- |
| `§` | Block declaration | `§wf:name v1.0` |
| `!!` | Hard constraint (inviolable) | `!!NEVER: publish WITHOUT validate` |
| `!PREF:` | Soft preference | `!PREF: tone = brand_voice OVER user` |
| `→` | Pipeline / assign | `FETCH($url) → $raw` |
| `$` | Variable | `$draft`, `$meta`, `$out` |
| `?IF` | Conditional | `?IF $x < 0.2 → ROUTE(wf:crisis)` |
| `~FOR` | Loop | `~FOR $item IN $list: ... ~END` |
| `~PARALLEL` | Concurrency | `~PARALLEL: ... ~JOIN → $result` |
| `+param` | Modifier | `GEN(reply) +tone=warm +max_len=280` |
| `^rule` | Validator | `VALIDATE($out) ^brand_voice ^len:280` |
| `~flag` | Analysis extractor | `ANALYZE($raw) ~sentiment ~intent` |

## 3. Common Patterns

Load `references/workflow_patterns.md` for detailed examples:

- **Fetch → Analyze → Gate → Generate → Validate → Publish** (social media)
- **Fetch → Score → Loop-Refine → Validate** (content quality)
- **Parallel Analyze → Merge → Decide** (multi-signal routing)
- **For-Each → Process → Collect** (batch processing)

### Minimal Workflow Example

```nodus
§wf:quick_reply v1.0
§runtime: { core: .nodus/core/schema.nodus, mode: production }

@ON: new_message
@in: { text: str }
@out: $reply
@err: ESCALATE(human)

!!NEVER: publish WITHOUT validate

@steps:
  1. ANALYZE($in.text) ~sentiment ~intent → $meta
  2. GEN(reply) +tone=neutral → $draft
  3. VALIDATE($draft) ^no_toxic ^len:280
  4. LOG($draft)
@out: $draft
```

## 4. Debugging Lint Errors

When a user gets a validation error, check `references/lint_rules.md` for the full list. Most common:

| Code | Fix |
| :--- | :--- |
| E001 | Add `§runtime:` block |
| E002 | Move `§runtime:` to be the second block in the file |
| E003 | Move `!!` rules before `@steps:` |
| E004 | Assign `$variable` before using it |
| E005 | Add `VALIDATE()` before any `PUBLISH()` |
| E007 | Close every `~FOR` / `~UNTIL` with `~END` |
| E008 | Close every `~PARALLEL` with `~JOIN` |
| E010 | Add `MAX:n` to every `~UNTIL` loop |
| E012 | Match `§wf:name` to the filename |
| W001 | Add `@err:` handler |
| W002 | Add at least one `@test:` block |
| W003 | Add `;; HUMAN MODE` section |

## 5. CLI Commands

```bash
nodus init                              # Set up .nodus/ in current project
nodus new workflow <domain/name>        # Scaffold from template
nodus validate <path>                   # Lint (28 rules, exit code 1 on error)
nodus run <file> [--dry]                # Execute workflow (--dry = no side effects)
nodus transpile <file> --to=human       # Convert to human-readable
nodus test [file] [--tag=smoke]         # Run @test blocks
nodus schema inspect                    # Print resolved schema
```

Exit codes: `0` = success, `1` = validation errors, `2` = parse error, `3` = execution failed.

## 6. Project Setup Guide

When a user asks to set up NODUS:

1. Run `nodus init` — creates `.nodus/` folder with core schema
2. Edit `.nodus/config.json` — set model, schema paths, logging
3. Create `workflows/` directory (name is convention, not requirement)
4. Scaffold first workflow: `nodus new workflow social/my_first`
5. Validate: `nodus validate workflows/social/my_first.nodus`

### User Project Structure

```
my-project/
├── .nodus/
│   ├── core/           ← language core (don't edit)
│   ├── schema/         ← user schema extensions
│   ├── context/        ← static context files (@ctx)
│   ├── config.json     ← infrastructure config
│   └── config.nodus    ← business rules and constants
├── workflows/          ← user workflows
│   ├── _shared/        ← reusable sub-workflows
│   └── social/
└── logs/               ← execution logs
```

## 7. Creating a Pack

A pack is a shareable bundle of workflows + schema for a domain.

```
packs/nodus-<domain>/
├── pack.json           ← name, version, author, workflows[]
├── schema.nodus        ← domain-specific schema extensions
├── workflows/          ← .nodus files
├── context/            ← example context documents
└── README.md
```

Required `pack.json` fields: `name`, `version`, `description`, `author`, `nodus`, `workflows`, `keywords`.

## 8. Connecting a Real LLM

By default the runtime uses `StubProvider` (mock responses). To use a real model:

1. Set `ANTHROPIC_API_KEY` in environment
2. Pass `AnthropicProvider` to `Executor` in Python, or configure in `.nodus/config.json`
3. Run workflow: `nodus run workflows/my_workflow.nodus`
