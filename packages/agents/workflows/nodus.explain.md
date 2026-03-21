---
description: Explain a .nodus workflow file in plain language — what it does, how it works, and what each symbol means.
---

# /nodus.explain

Read a NODUS workflow and explain it to the user in plain, accessible language.

## Steps

1. **Identify the target file.** If the user has a `.nodus` file open, use it. Otherwise ask.

2. **Read and parse the file** content.

3. **Provide a high-level summary:**
   - What this workflow does (one sentence)
   - When it triggers (`@ON:`)
   - What it takes as input (`@in:`)
   - What it produces (`@out:`)

4. **Walk through each section:**

   - **`§runtime:`** — what schema it uses, what model runs it, what mode
   - **`!!` rules** — what constraints are inviolable and why they matter
   - **`!PREF:` preferences** — what defaults are set for ambiguous decisions
   - **`@ctx:`** — what context files are loaded and what they provide
   - **`@err:`** — what happens if something goes wrong

5. **Walk through `@steps:` one by one.** For each step:
   - What command is called and what it does
   - What input it takes and what output it produces
   - Any conditionals (`?IF`), loops (`~FOR`, `~UNTIL`), or parallel (`~PARALLEL`) blocks
   - Any modifiers (`+param`) or validators (`^rule`)

6. **Explain the HUMAN MODE section** if present — confirm it matches the steps.

7. **Explain the `@test:` blocks** — what scenarios are tested.

8. **Summarize with a flow diagram** using text:
   ```
   trigger → fetch → analyze → [gate] → generate → validate → publish → log
   ```

9. **Offer next actions:**
   - "Validate this workflow?" → `/nodus.validate`
   - "Run this workflow?" → suggest `nodus run <file>`
   - "Any questions about specific symbols?" → reference `.agents/skills/nodus/references/syntax_cheatsheet.md`
