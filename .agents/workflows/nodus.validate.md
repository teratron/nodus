---
description: Validate a .nodus workflow file and explain any errors with suggested fixes.
---

# /nodus.validate

Validate a NODUS workflow and provide human-friendly explanations for every issue found.

## Steps

1. **Identify the target.** If user has a `.nodus` file open, use it. If a directory is given, validate all `.nodus` files in it. Otherwise ask.

// turbo
2. **Run validation** — execute `nodus validate <target>` in the project root.

3. **Parse the output.** Group diagnostics by severity:
   - **Errors (E)** — must be fixed before the workflow can run
   - **Warnings (W)** — risky but won't block execution
   - **Info (I)** — style suggestions

4. **For each diagnostic**, provide:
   - The lint code and message (e.g. `[E005] PUBLISH requires prior VALIDATE`)
   - A plain-language explanation of WHY this is a problem
   - A concrete fix — show the exact code change needed
   - Reference the rule from `.agents/skills/nodus/references/lint_rules.md`

5. **Offer to auto-fix.** For simple issues (missing `@err:`, missing `MAX:n`, unclosed `~END`), offer to apply fixes directly.

6. **Re-validate** after fixes are applied to confirm all issues are resolved.

7. **Report final status:**
   - ✅ "Workflow is valid and ready to run"
   - ⚠️ "Workflow has N warnings but can run"
   - ❌ "Workflow has N errors that must be fixed"
