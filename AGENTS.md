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

* [ ] **Validated**: All quality checks pass with zero warnings:
  * `uv run ruff check --fix` & `uv run ruff format`
  * `uv run pyrefly check`
  * `uv run pytest`
* [ ] **Versioned**: Increment the patch version (e.g., `0.4.2` → `0.4.3`) in:
  * `pyproject.toml`
  * `packages/runtime/constants.py`
  * `packages/spec/VERSION`
  * `CHANGELOG.md`
  * **Engine**: If content in `packages/spec/core/` or `packages/agents/workflows/` was modified, follow **Rule 2.3 (C14)** to update engine meta and version.
* [ ] **Documented**:
  * Update `CHANGELOG.md` with a summary of changes.
  * Update `README.md` if public API or features were changed.
  * Update relevant `docs/` or specs (e.g. `docs/cli.md`) to reflect task completion.
* [ ] **Synchronized**: Run `uv sync` to ensure `uv.lock` is up to date after `pyproject.toml` changes.
  * **Hardlinks**: Verify integrity with `fsutil hardlink list AGENTS.md` (should show 3 files). If broken, run `nodus-dev-init` to restore.
* [ ] **Preserved**: Verify that structural documents (like diagrams or `STRUCTURE.md`) haven't lost data during edits.

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

* Avoid standard PEP8 horizontal lines or excessive whitespace. Use Unicode box characters to create a clean, modern look.

## 6. Windows Junction Safety

When managing Windows junctions (`mklink /J`) and git index, follow this strict order to prevent data loss:

### 6.1 The Problem

`git rm -r --cached <path>` on Windows **follows junctions** and physically deletes files in the
junction target, even with `--cached`. Example: `git rm -r --cached demo/.nodus/core` where
`demo/.nodus/core` is a junction to `packages/spec/core/` will **delete all files in `packages/spec/core/`
from disk**.

### 6.2 Safe Procedure

Always run `git rm --cached` **before** creating junctions, while the paths are empty or nonexistent:

```
1. git rm --cached   ← first, while no junctions exist yet
2. mklink /J ...     ← then create junctions
```

When removing from git index, list **specific file paths** rather than directories:

```bash
# Safe — specific files only
git rm --cached --ignore-unmatch .agents/workflows/nodus.compile.md ...

# Dangerous — git will traverse the junction into packages/
git rm -r --cached .agents/skills/nodus
```

## 7. File Interaction Protocol

To prevent accidental data loss or corruption in large documents, the agent MUST follow this protocol:

### 7.1 Pre-read Requirement

* **Mandatory**: Always read the target file BEFORE making any edits.
* **Scope**: Read the entire file if it's within tool limits to ensure full context.
* **Anti-Pattern**: DO NOT rely on cached or partial information from previous steps.

### 7.2 Post-verify Requirement

* **Verification**: Immediately after an edit, read the file or search its contents to verify the result.
* **Integrity**: Check that surrounding code or documentation blocks (like diagrams) were NOT affected by the edit.
* **Recovery**: If data was lost, restore it immediately before proceeding.
