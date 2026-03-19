---
description: Execute a .nodus workflow with validation, input preparation, and structured result reporting.
---

# /nodus.run

Execute a NODUS workflow with full pre-flight checks and result reporting.

## Steps

// turbo

1. **Check CLI availability** — run `nodus --version`. If the command is not found, stop and tell the user: "The `nodus` CLI is not installed. Run `pip install nodus` and try again."

2. **Identify the target file.** If user has a `.nodus` file open, use it. Otherwise ask.

3. **Ask upfront: dry run?** — "Do you want a dry run (no side effects, no publishes)?" If yes, use `--dry` flag in step 5.

// turbo
4. **Pre-flight validation** — run `nodus validate <file>`. If errors exist, report and stop. Offer `/nodus.validate` to fix.

5. **Prepare input data.** Read the `@in:` contract from the file and present two sections:

   **Required fields** — ask the user for each value:

   ```
   text (str): ?
   user_id (str): ?
   ```

   **Optional fields** — show defaults, ask only if user wants to override:

   ```
   tone (str) = "neutral" — override? (press Enter to keep)
   max_len (int) = 280 — override? (press Enter to keep)
   ```

// turbo
6. **Execute** — run `nodus run <file> [key=val ...] [--dry]` with the prepared input.

7. **Parse the `NODUS:RESULT` output** and present:
   - **Status:** SUCCESS ✅ / PARTIAL ⚠️ / FAILED ❌ / ABORTED 🛑
   - **Output (`$out`):** formatted and readable
   - **Execution log:** step-by-step trace (last 10 entries)
   - **Errors:** if any, with explanations

8. **For failures**, diagnose:
   - Which step failed and why
   - Was a `!!` rule violated?
   - Did a `~UNTIL` loop hit `MAX:n`?
   - Was a variable undefined?
   - Suggest a fix

9. **Offer next actions:**
   - "Run again with different input?"
   - "View in HUMAN mode?" → `nodus transpile <file> --mode human`
   - "Run tests?" → `/nodus.test`
