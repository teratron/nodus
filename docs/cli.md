# NODUS CLI

The `nodus` CLI is the primary interface for working with NODUS workflows.
It is implemented in Python and installed as a single entry point via `pip install nodus-lang`.

## Installation

```bash
pip install nodus-lang
nodus --version
```

For other installation methods see the [Contributing guide](../CONTRIBUTING.md#installation-architecture).

## Commands

| Command | Usage | Description |
| :--- | :--- | :--- |
| `init` | `nodus init` | Scaffold `.nodus/` folder in current project. |
| `new workflow` | `nodus new workflow <domain/name>` | Create a workflow from template. |
| `validate` | `nodus validate <path>` | Lint a workflow — checks all 28 rules. |
| `run` | `nodus run <file> [--dry]` | Validate and execute a workflow. |
| `transpile` | `nodus transpile <file> --to=human` | Convert between NODUS and HUMAN modes. |
| `test` | `nodus test [file] [--tag=name]` | Execute `@test` blocks. |
| `schema inspect` | `nodus schema inspect` | Print the resolved project schema. |

## Command Flags

- `--dry`: Simulate workflow steps without side effects or publishing.
- `--to=human` / `--to=nodus`: Target mode for `transpile`.
- `--tag=<name>`: Filter `@test` blocks by tag (e.g. `--tag=smoke`).
- `--force`: Overwrite existing files when scaffolding.
- `--save`: Write transpile output to a file.

## Exit Codes

| Code | Meaning |
| :--- | :--- |
| `0` | Success |
| `1` | Validation errors (E-level lint rules) |
| `2` | Parse error |
| `3` | Execution failed |

## Structured Output

Every `nodus run` execution returns a `NODUS:RESULT` object:

```
NODUS:RESULT {
  status:  SUCCESS | PARTIAL | FAILED | ABORTED
  out:     <final output payload>
  log:     <execution history>
  errors:  <list of failures>
  flags:   <execution flags>
}
```

## Validation Output

`nodus validate` reports diagnostics by severity:

```
[E001] §runtime: block required but not found
[W001] No @err handler declared
[I003] No @test block tagged 'smoke'
```

- `E` — Error: blocks execution
- `W` — Warning: unsafe but runnable
- `I` — Info: style suggestion

## Assistant Behavior Rules

When executing CLI commands the assistant follows these strict rules:

- **Confirm Overwrites**: Never overwrite a file without asking the user.
- **Auto-Validate**: Always validate a workflow before running it.
- **Surface Ambiguity**: If a path or command is unclear, stop and ask.
- **Structured Logs**: Always report a `NODUS:RESULT` after command completion.

## Initialization Flow

`nodus init` performs these steps:

```
1. Detect runtime (python3 → uv → standalone binary)
2. Create .nodus/ folder structure
3. Download core/ from GitHub releases
4. Scaffold config.json (interactive wizard or defaults)
5. Scaffold config.nodus (base !! rules)
6. Update .gitignore
7. Report: ✓ NODUS initialized
```
