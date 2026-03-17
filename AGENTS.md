# Agent Rules & Guidelines

## 1. Language Policy

Consistency in communication and code is paramount.

### 1.1 Technical Content (English ONLY)

* Codebase: All identifiers (variables, functions, classes), comments, and docstrings.
* Documentation: Technical guides, READMEs, and implementation notes.
* Process: Commit messages, PR descriptions, and issue titles.
* Environment: Error messages, logs, and API definitions.

### 1.2 Communication (Russian)

* Chat Interaction: Discussions, explanations, and project planning.
* Decision Making: Strategic choices and high-level feature discussions.
* Reviews: Conversational feedback during pair programming.

## 2. Markdown Guidelines

* **Separators**: Avoid horizontal rules (`---`). Use them only in the footer if absolutely necessary.
* **Links**: No hardcoded absolute links (e.g., `file:///D:/...`). Use relative paths or just backticks for filenames (e.g., `pyproject.toml`).

## 3. Development Toolchain

The project strictly adheres to **uv-first** philosophy.

### 3.1 Virtual Environment

Always initialize and activate the environment before execution:

```powershell
# Initialization
uv sync

# Activation (Windows)
.venv\Scripts\activate
```

```bash
# Linting & Formatting
uv run ruff check --fix
uv run ruff format

# Static Analysis
uv run pyright

# Verification
uv run pytest
```

## 4. Completion Protocol

Follow this checklist before declaring a task finished:

* [ ] **Validated**: All quality checks pass with zero warnings.
* [ ] **Versioned**: Increment the patch version (e.g., `0.3.1` → `0.3.2`) in:
  * `pyproject.toml`
  * `runtime/cli/nodus.py`
  * `CHANGELOG.md`
* [ ] **Documented**: Update `README.md`, `CHANGELOG.md`, and internal docs to reflect all changes.
* [ ] **Synchronized**: Run `uv sync` to ensure `uv.lock` is up to date.
