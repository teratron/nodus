---
description: Validate a .nodus workflow file and explain any errors with suggested fixes.
---

# /nodus.validate

Validate a NODUS workflow and provide human-friendly explanations for every issue found.

## Steps

// turbo

1. **Check CLI availability** — run `nodus --version`. If the command is not found, stop and tell the user: "The `nodus` CLI is not installed. Run `pip install nodus` and try again."

2. **Identify the target.** If user has a `.nodus` file open, use it. If a directory is given, validate all `.nodus` files in it. Otherwise ask.

// turbo
3. **Run validation** — execute `nodus validate <target>` in the project root.

4. **Parse the output.** Group diagnostics by severity:

   - **Errors (E)** — must be fixed before the workflow can run
   - **Warnings (W)** — risky but won't block execution
   - **Info (I)** — style suggestions

5. **For each diagnostic**, provide:
   - The lint code and message (e.g. `[E005] PUBLISH requires prior VALIDATE`)
   - A plain-language explanation of WHY this is a problem
   - A concrete fix — show the exact code change needed
   - Reference the rule from `.agents/skills/nodus/references/lint_rules.md`

6. **Offer to auto-fix** only for issues with known mechanical fixes. Apply fixes only for these codes:

   | Code | Auto-fix action |
   | :--- | :--- |
   | W001 | Append `@err: ESCALATE(human)` before `@steps:` |
   | E007 | Close the open `~FOR` / `~UNTIL` block with `~END` |
   | E008 | Close the open `~PARALLEL` block with `~JOIN → $result` |
   | E010 | Add `MAX:10` to the `~UNTIL` loop (ask user for preferred value first) |

   For any other code, explain the fix but require the user to apply it manually.

7. **Re-validate** after fixes are applied to confirm all issues are resolved.

8. **Report final status:**
   - ✅ "Workflow is valid and ready to run"
   - ⚠️ "Workflow has N warnings but can run"
   - ❌ "Workflow has N errors that must be fixed"
