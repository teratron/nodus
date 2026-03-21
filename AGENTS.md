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
* **Links**: No hardcoded absolute links (e.g., `file:///C:/...`). Use relative paths or just backticks for filenames (e.g., `pyproject.toml`).

## 3. Development Toolchain

The project strictly adheres to **uv-first** philosophy.

### 3.1 Virtual Environment

Always initialize and activate the environment before execution:

```bash
# Initialization
uv sync

# Activation (Windows)
.venv\Scripts\activate

# Activation (Linux)
source .venv/bin/activate
```

```bash
# Linting & Formatting
uv run ruff check --fix
uv run ruff format

# Static Analysis
uv run pyrefly check

# Verification
uv run pytest
```

## 4. Completion Protocol

Follow this checklist before declaring a task finished:

* [ ] **Validated**: All quality checks pass with zero warnings.
* [ ] **Versioned**: Increment the patch version (e.g., `0.3.1` → `0.3.2`) in:
  * `pyproject.toml`
  * `runtime/constants.py`
  * `CHANGELOG.md`
* [ ] **Documented**: Update `README.md`, `CHANGELOG.md`, and internal docs to reflect all changes.
* [ ] **Synchronized**: Run `uv sync` to ensure `uv.lock` is up to date.
* [ ] **Preserved**: Verify that structural documents (like diagrams) haven't lost data.

## 5. Python Coding Style

All Python source files must adhere to a premium and uniform visual style.

### 5.1 Documentation (Google Style)

* Use Google-style docstrings for all functions, methods, and classes.
* Include `Args:`, `Returns:`, and `Raises:` sections where applicable.
* Maintain `from __future__ import annotations` at the top of every file.

### 5.2 Navigation & Section Blocks

Use consistent Unicode-based separators to improve code readablity:

* **Major Sections** (File-level, Classes, Public API):

    ```python
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION NAME (ALL CAPS)
    # ═══════════════════════════════════════════════════════════════════════════
    ```

* **Minor Sections** (Internal logic groups, Utility functions):

    ```python
    # ───────────────────────────────────────────────────────────────────────────
    # Sub-section Name (Title Case)
    # ───────────────────────────────────────────────────────────────────────────
    ```

* Avoid standard standard PEP8 horizontal lines or excessive whitespace. Use Unicode box characters to create a clean, modern look.

## 6. File Interaction Protocol

To prevent accidental data loss or corruption in large documents, the agent MUST follow this protocol:

### 6.1 Pre-read Requirement

* **Mandatory**: Always call `view_file` on the target file BEFORE making any edits.
* **Scope**: Read the entire file if it's within tool limits (800 lines) to ensure full context.
* **Anti-Pattern**: DO NOT rely on cached or partial information from previous steps.

### 6.2 Post-verify Requirement

* **Verification**: Immediately after an edit, use `view_file` or `run_command` (grep/dir) to verify the result.
* **Integrity**: Check that surrounding code or documentation blocks (like diagrams) were NOT affected by the edit.
* **Recovery**: If data was lost, restore it immediately before proceeding.
