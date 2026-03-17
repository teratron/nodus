# Agent Rules

## Language Preferences

### Brief overview

This set of guidelines outlines language preferences for the project, ensuring consistency in code and communication.

### Code and documentation language

- All code, comments, documentation, variable names, function names, class names, method names, attribute names, and technical terms must be in English
- Maintain English as the primary language for all technical elements including error messages, log entries, configuration keys, and API responses to ensure readability and maintainability
- Technical documentation, inline comments, docstrings, and README files must be written in English
- All commit messages, pull request descriptions, and issue titles related to code changes should be in English

### Communication style

- Explanations and discussions in the chat interface should be in Russian
- Use Russian for conversational responses, clarifications, project planning, and non-technical interactions
- Project management communications, feature discussions, and strategic decisions should be conducted in Russian
- Code review comments and technical discussions during development can be in Russian unless collaborating with English-speaking developers

## Toolchain

This project uses **uv** as the package manager. Prefer native uv commands (`uv run`, `uv sync`, `uv add`) over pip-compatible wrappers (`uv pip install`) wherever possible.

Before running any commands, activate the virtual environment:

- **Windows:** `.venv\Scripts\activate`
- **Unix/macOS:** `source .venv/bin/activate`

If `.venv` does not exist, create it first:

```bash
uv sync
```

## Quality Checks

Run these before committing:

```bash
# Lint and auto-fix (including warnings)
ruff check --fix
ruff format

# Type checking
pyright

# Tests
pytest
```

All three must pass with zero errors and zero warnings before any commit.
