# Testing Strategy
**Version:** 1.0.0
**Status:** Draft
**Layer:** L1

## Overview
This specification outlines the comprehensive testing strategy for the Nodus multi-package ecosystem. It covers unit testing layout, testing frameworks, and continuous integration targets.

## Motivation
Given a modular setup comprising multiple decoupled architectural elements, strict consistency in testing strategies must be maintained to catch cross-package failures.

## Approach
- **Unit Testing**: Leveraging `pytest` on all core packages.
- **Linters**: Format checking and standard linting via `ruff` and `pyrefly`.
- **Isolation Boundaries**: Core dependencies should be mocked to strictly test isolated logic paths.

## Related Specifications
- `l1-nodus-architecture.md`

## Document History
| Version | Date | Description |
| :--- | :--- | :--- |
| 1.0.0 | 2026-03-30 | Initial scaffolding |
