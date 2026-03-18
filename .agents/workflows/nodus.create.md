---
description: Interactively create a new NODUS workflow from scratch with guided questions.
---

# /nodus.create

Guide the user through creating a new `.nodus` workflow step by step.

## Steps

1. **Ask the domain and name.** Example: `social/reply_to_mention`. The name must be `snake_case`.

2. **Ask what the workflow does** — one sentence describing its purpose.

3. **Ask about the trigger.** Multiple choice:
   - Event-based (`@ON: new_mention`)
   - Scheduled (`@ON: schedule:09:00`)
   - Webhook (`@ON: webhook:event_key`)
   - Manual (no `@ON:`, run via CLI)

4. **Ask about inputs.** What data does the workflow receive? Ask for field names, types, and which are optional. Reference types from `.agents/skills/nodus/references/syntax_cheatsheet.md` → Type System.

5. **Ask about key constraints.** What must NEVER happen? What should ALWAYS happen? These become `!!` rules.

6. **Ask about context files.** Does the workflow need brand voice, guidelines, or other context loaded via `@ctx:`?

// turbo
7. **Scaffold the file** — run `nodus new workflow <domain/name>` in the project root.

8. **Fill in the template** with gathered information:
   - `§wf:name v1.0` header
   - `§runtime:` block
   - `@ON:` trigger
   - `!!` rules and `!PREF:` preferences
   - `@in:` / `@out:` / `@ctx:` / `@err:` declarations
   - `@steps:` — generate logical steps based on the purpose
   - `;; HUMAN MODE` section
   - `@test:` block with at least one `+tag=smoke` test

9. **Show the result** to the user for review. Highlight each section.

// turbo
10. **Validate** — run `nodus validate <file>` to confirm correctness.

11. **Report** — if clean, congratulate. If issues, fix them and re-validate.
