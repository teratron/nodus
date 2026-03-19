# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-03-19

### Added

- **Syntactic Sugar (v0.7)**: Quality-of-life constructs for cleaner, more expressive workflows.
  - `?SWITCH` — multi-branch dispatch on a single value (replaces repetitive `?IF/?ELIF` chains).
  - `~RETRY:n` — step-level retry modifier with optional `+backoff` and `+retry_on` params.
  - `?.` — optional chaining: short-circuits to `null` if any path segment is absent.
  - `WHERE` — inline collection filter using implicit `$it` variable.
  - `FIRST` / `LAST` — access first or last item in a collection, with optional `WHERE` filter.
  - `~MAP` — single-line collection transform (one command applied to every item).
  - String interpolation — `$var` and `$obj.field` expand inside string literals.
- **Error**: `NODUS:SWITCH_NO_MATCH` — emitted when `?SWITCH` has no matching arm and no `*` wildcard.
- **Lint**: `E014` — `~RETRY` without explicit `:n` count; `W012` — `?SWITCH` without `*` wildcard.

### Changed

- `schema.nodus` → v0.7; `schema.errors.nodus` → v0.7; `schema.lint.nodus` → v0.7.
- `AGENTS.md` → v0.7 with §3 sections for all new constructs.

---

## [0.6.0] - 2026-03-19

### Added

- **Human Interaction Protocol**: AI ↔ Human dialogue primitives.
  - `ASK(prompt)` — inline blocking question; workflow resumes automatically after response.
  - `CONFIRM(content)` — present content and request approval; supports custom action labels.
  - `dialog_type` enum: `str | bool | confirm | choice | multi_choice`.
  - `dialog_result` type.
  - `NODUS:DIALOG_TIMEOUT` (C022) — ASK/CONFIRM timeout error.
  - `NODUS:DIALOG_REJECTED` (C023) — CONFIRM with `+strict=true` rejected.
- `AGENTS.md` §12 Human Interaction Protocol.

### Changed

- `schema.nodus` → v0.6; `schema.types.nodus` → v0.6; `schema.errors.nodus` → v0.6.

---

## [0.5.0] - 2026-03-19

### Added

- **Schema Modularization**: Non-runtime sections extracted from `schema.nodus`.
  - `schema.lint.nodus` — §lint rules; load only from `nodus validate`. Never at runtime.
  - `schema.tests.nodus` — §testing spec; load only from `nodus test`. Never at runtime.
  - `@needs:` directive — selective section loading from `extends:` schemas.
    - Flat form: `@needs: [§commands_sdd, §macros_sdd]`
    - Keyed form: `@needs: { "sdd.schema.nodus": [...] }`
  - `"modules"` key in `nodus.config.json` — tooling discovery for lint/test modules.
- **AGENTS.md** §7 rewritten: §7.1–§7.4 covering core, extensions, `@needs:`, fallback.
- **Token efficiency**: `schema.nodus` reduced from 852 → 613 lines (−29% per execution).

### Changed

- `schema.nodus` → v0.5 (§lint and §testing removed; `@needs:` added to §syntax).
- All 8 SDD pack workflows updated with `@needs:` in `§runtime`.
- `workflow.template.nodus` — `@needs:` commented example added.

---

## [0.4.1] - 2026-03-19

### Added

- **NODUS Core Enhancements (v0.4)**: Addressed language gaps identified during complex workflow translation.
  - New Core Commands: `READ_FILE`, `SCAN_DIR`, `ENV`, `DATE`, `COUNTER`, `GIT`, `QUERY_GIT`.
  - New System Commands: `MOVE`, `COPY`, `TRANSPILE`, `HASH`, `PARSE_MD_HEADER`, `PARSE_INDEX`, `VERSION_BUMP`, `GENERATE_DOC`.
  - Operator: `MATCHES` (deterministic regex pattern matching).
  - Keywords: `!HALT` (fatal stop), `!PAUSE` (approval-gate suspend).
  - Types: `date_expr`, `workspace_config`, `workspace_cfg`, `counter_state`, `git_result`.
  - Lint Rules: `E013` (version compatibility), `W011` (parallel branch error isolation).
- **Triggers**: Added optional `priority` parameter to `@ON` triggers.

### Changed

- Updated `schema.nodus`, `schema.types.nodus`, and `schema.errors.nodus` to version 0.4.
- Synchronized `KNOWN_COMMANDS` in `constants.py` with the updated core schema.

### Changed

- **Project Restructure**: Migrated to monorepo `packages/` layout.
  - `lang/core/` → `packages/spec/core/` (language specification).
  - `lang/templates/` → `packages/spec/templates/`.
  - `lang/examples/` → `examples/` (root level).
  - `runtime/` → `packages/runtime/` (Python runtime).
  - `extensions/` → `packages/extensions/` (IDE support).
  - `demo/.nodus/config.nodus` → `demo/config.nodus` (project-level config).
  - Created `packages/spec/VERSION` for independent spec versioning.
  - Created junction link `demo/.nodus/core/` → `packages/spec/core/`.
- Updated `pyproject.toml` paths for new layout (`packages/runtime`).
- Updated `settings.py` `DEFAULT_SCHEMA_PATH` → `packages/spec/core/schema.nodus`.
- Updated `README.md`, `CONTRIBUTING.md`, `docs/` with new structure references.

### Removed

- `lang/` directory (contents moved to `packages/spec/` and `examples/`).
- `sandbox/` directory (empty, unused).

## [0.3.8] - 2026-03-17

### Added

- **Premium Python Code Style**: Implemented a unified visual style for all Python files as defined in `AGENTS.md`.
  - Major sections use double-line Unicode separators (`═══════════════════════════════════════════════════════════════════════════`).
  - Minor sections use single-line Unicode separators (`───────────────────────────────────────────────────────────────────────────`).
  - Strict Google-style docstrings enforced for all functions, methods, and classes.
  - Type annotations and `from __future__ import annotations` added to all modules.

### Changed

- Updated `AGENTS.md` with the new Python coding style guidelines and Unicode-based section blocks.
- Refactored `runtime/interpreter/`, `runtime/cli/`, and `tests/runtime/` to adhere to the new style.

## [0.3.7] - 2026-03-17

### Fixed

- `find_config()` simplified to canonical `.nodus/config.json` — removed stale `config.json` and `nodus.config.json` fallback paths.
- `workflows/beautiful_mention.nodus`: `§runtime.core` path corrected from `../../core/schema.nodus` to `.nodus/core/schema.nodus`.
- `config.nodus` (root): `§runtime.core` and all inline comments updated from `./core/schema.nodus` / `nodus.config.json` to `.nodus/core/schema.nodus` / `.nodus/config.json`.
- `settings.py` `NEW_WORKFLOW_TEMPLATE`: `core/schema.nodus` → `.nodus/core/schema.nodus` (consistent with template).
- `.nodus/config.json`: `nodus/core/schema.nodus` → `.nodus/core/schema.nodus`.
- `cmd_init`: unused `_ = args` removed (renamed parameter to `_args`).

### Added

- `cmd_new` now supports `domain/name` syntax: `nodus new social/reply` creates `workflows/social/reply.nodus` with parent directories scaffolded automatically.
- `nodus init` now scaffolds `config.nodus` (business logic layer) from a built-in template. Existing file is never overwritten.
- `settings.py`: added `NEW_CONFIG_NODUS_TEMPLATE` for the scaffolded `config.nodus`.
- `packs/nodus-social/pack.json`: added `workflows` and `keywords` fields required by CONTRIBUTING spec.
- `README.md`: added "Connecting a Real LLM Provider" section with a working `ClaudeProvider` example and `ANTHROPIC_API_KEY` setup instructions.

## [0.3.6] - 2026-03-17

### Changed

- Updated `README.md`: added Quick Start section, corrected status to v0.3.6, updated roadmap to reflect Python runtime completion.
- Updated `CONTRIBUTING.md`: fixed `tests/` directory path (`runtime/tests/` → `tests/runtime/`), added missing files (`pyproject.toml`, `CHANGELOG.md`, `grammar.peg`, `constants.py`, `settings.py`), updated release roadmap, added `uv run pytest` to Running Tests section.
- Rewrote `docs/cli.md`: describes the actual Python CLI (commands, flags, exit codes, output format, init flow).
- Rewrote `docs/schema.md`: expanded from 7 to 24 commands, added all 16 reserved variables, added missing analysis flags (`~toxicity`, `~entities`, `~lang`, `~pii`), added Error Codes section.
- Rewrote `docs/syntax.md`: added `§runtime:`, `@ctx:`, `@err:`, `@macro:`, `@test:`, comment syntax (`;` / `;;`), `!BREAK`/`!SKIP`, `$CFG.*` constants, `~END` closer.
- Updated `docs/protocol.md`: bumped protocol version to v0.3, added `flags` to Result Contract, added 3 missing Prohibited Actions.
- Updated `docs/README.md`: corrected project structure references, bumped version footer to v0.3.6.

## [0.3.5] - 2026-03-17

### Added

- Comprehensive docstrings and comments across all `runtime/interpreter` files (`parser.py`, `lexer.py`, `transpiler.py`, `validator.py`, `ast_nodes.py`).

### Changed

- Refactored `transpiler.py`, `executor.py`, and `validator.py` to use a centralized `constants.py` for static strings and mappings.
- Improved code clarity and maintainability in the runtime core.

## [0.3.4] - 2026-03-17

### Changed

- Updated `AGENTS.md` with new Markdown generation and formatting rules.
- Cleaned up `README.md`, `CONTRIBUTING.md`, and other docs to follow new guidelines (no horizontal separators, no absolute links).

## [0.3.3] - 2026-03-17

### Fixed

- Resolved `PytestCollectionWarning` by renaming AST node `TestBlock` to `NodusTestBlock`.
- Added `__test__ = False` to `NodusTestBlock` to explicitly exclude it from pytest discovery.

## [0.3.2] - 2026-03-17

### Changed

- Refactored `AGENTS.md` for better clarity and structure.
- Formalized `Completion Protocol` for quality control.

## [0.3.1] - 2026-03-17

### Added

- Added `Finalizing Changes` rule to `AGENTS.md`.
- Integrated `Ruff` and `Pyright` as primary quality tools.

### Removed

- Removed `Pylint` from the project (replaced by Ruff).
- Removed all `pylint: disable` comments from the codebase.

### Changed

- Updated `pyproject.toml` with Ruff configuration and McCabe complexity threshold (30).
- Renamed internal maps to follow PEP8 naming conventions.

## [0.3.0] - 2026-03-17

### Added

- Mandatory `§runtime:` block enforcement in linter (E001).
- Comprehensive test suite for Lexer, Parser, and Validator.
- CLI support for `validate`, `run`, `transpile`, and `test`.

### Fixed

- Corrected `templates/schema.template.nodus` structure.
- Updated `templates/workflow.template.nodus` with project-relative paths.
- Synchronized `examples/` with current specification requirements.

### Technical

- Initial formal grammar definition in `core/grammar.peg`.
- Modernized build system using `uv`.
