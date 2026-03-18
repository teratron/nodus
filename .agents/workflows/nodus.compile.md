---
description: Full compile cycle for a .nodus workflow — parse, validate, transpile, report.
---

# /nodus.compile

Run the full compilation pipeline for a NODUS workflow file.

## Steps

1. **Identify the target file.** If the user has a `.nodus` file open, use it. Otherwise ask which file to compile.

2. **Read the file** and check it exists and has `.nodus` extension.

// turbo
3. **Validate** — run `nodus validate <file>` in the project root.

4. **Report validation results:**
   - If errors (E-level): list each error with explanation and suggested fix. Reference `.agents/skills/nodus/references/lint_rules.md` for details. **Stop here** — do not proceed to transpile.
   - If warnings only (W-level): list warnings, note they are non-blocking, continue.
   - If clean: report "✓ No issues found".

// turbo
5. **Transpile to HUMAN mode** — run `nodus transpile <file> --mode human`.

6. **Present the result** to the user:
   - Show the HUMAN-mode output
   - Summarize: workflow name, version, trigger, number of steps, input/output contract
   - If warnings were found in step 4, remind the user

7. **Offer next actions:**
   - "Run this workflow?" → `/nodus.run`
   - "Fix warnings?" → explain each warning and suggest edits
   - "Run tests?" → `/nodus.test`
