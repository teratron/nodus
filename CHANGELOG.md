# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
