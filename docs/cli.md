# NODUS CLI Protocol

The NODUS CLI is a meta-workflow (`cli.nodus`) that defines how the AI Assistant manages projects and workflows.

## 1. Core Commands

| Command | Usage | Description |
| :--- | :--- | :--- |
| `init` | `nodus init <name>` | Scaffolds a new project structure. |
| `new workflow` | `nodus new workflow social/reply` | Creates a workflow from template. |
| `validate` | `nodus validate <path>` | Checks syntax and schema compliance. |
| `run` | `nodus run <file> [--dry]` | Runs a workflow (validates first). |
| `transpile` | `nodus transpile <file> --to=human` | Converts between NODUS and HUMAN modes. |
| `test` | `nodus test [file] [--tag=name]` | Executes `@test` blocks. |
| `schema` | `nodus schema inspect` | Prints the resolved project schema. |

## 2. Command Flags

- `--dry`: Simulate workflow steps without making real changes or publishing.
- `--human`: Output results in human-readable prose.
- `--force`: Overwrite existing files when creating new ones.
- `--save`: Save transpile result to a file.

## 3. Assistant Behavior (Rules)

When executing CLI commands, the assistant follows these strict rules:

- **Confirm Overwrites**: Never overwrite a file without asking the user.
- **Auto-Validate**: Always validate a workflow before running it.
- **Surface Ambiguity**: If a path or command is unclear, stop and ask.
- **Structured Logs**: Always report a `NODUS:RESULT` after command completion.

## 4. Initialization Template

New workflows are initialized using `workflow.template.nodus`, ensuring standard headers, runtime blocks, and trigger declarations.
