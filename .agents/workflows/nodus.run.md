---
description: Execute a .nodus workflow with validation, input preparation, and structured result reporting.
---

# /nodus.run

Execute a NODUS workflow with full pre-flight checks and result reporting.

## Steps

1. **Identify the target file.** If user has a `.nodus` file open, use it. Otherwise ask.

// turbo
2. **Pre-flight validation** — run `nodus validate <file>`. If errors exist, report and stop. Offer `/nodus.validate` to fix.

3. **Prepare input data.** Read the `@in:` contract from the file:
   - List required fields with types
   - List optional fields with defaults
   - Ask the user for values for required fields
   - Use `--dry` flag if the user wants a dry run (no side effects)

// turbo
4. **Execute** — run `nodus run <file> [key=val ...]` with the prepared input.

5. **Parse the `NODUS:RESULT` output** and present:
   - **Status:** SUCCESS ✅ / PARTIAL ⚠️ / FAILED ❌ / ABORTED 🛑
   - **Output (`$out`):** formatted and readable
   - **Execution log:** step-by-step trace (last 10 entries)
   - **Errors:** if any, with explanations

6. **For failures**, diagnose:
   - Which step failed and why
   - Was a `!!` rule violated?
   - Did a `~UNTIL` loop hit `MAX:n`?
   - Was a variable undefined?
   - Suggest a fix

7. **Offer next actions:**
   - "Run again with different input?"
   - "View in HUMAN mode?" → `nodus transpile <file> --mode human`
   - "Run tests?" → `/nodus.test`
