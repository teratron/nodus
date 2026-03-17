# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
