---
description: Interactively create a new NODUS workflow from scratch with guided questions.
---

# /nodus.create

Guide the user through creating a new `.nodus` workflow step by step.

## Steps

// turbo

1. **Check CLI availability** — run `nodus --version`. If the command is not found, stop and tell the user: "The `nodus` CLI is not installed. Run `pip install nodus` and try again."

2. **Ask the domain and name.** Example: `social/reply_to_mention`. The name must be `snake_case`.

3. **Ask what the workflow does** — one sentence describing its purpose.

4. **Ask about the trigger.** Multiple choice:
   - Event-based (`@ON: new_mention`)
   - Scheduled (`@ON: schedule:09:00`)
   - Webhook (`@ON: webhook:event_key`)
   - Manual (no `@ON:`, run via CLI)

5. **Ask about inputs.** What data does the workflow receive? For each field ask:

   - Field name
   - Type: `str`, `int`, `float`, `bool`, `list`, `dict`, or `enum[val1,val2]`
   - Required or optional? If optional, what is the default?

6. **Ask about key constraints.** What must NEVER happen? What should ALWAYS happen? These become `!!` rules.

7. **Ask about context files.** Does the workflow need brand voice, guidelines, or other context loaded via `@ctx:`?

// turbo
8. **Scaffold the file** — run `nodus new workflow <domain/name>` in the project root.

9. **Fill in the template** with gathered information:
   - `§wf:name v1.0` header
   - `§runtime:` block
   - `@ON:` trigger
   - `!!` rules and `!PREF:` preferences
   - `@in:` / `@out:` / `@ctx:` / `@err:` declarations
   - `@steps:` — generate logical steps based on the purpose
   - `;; HUMAN MODE` section
   - `@test:` block with at least one `+tag=smoke` test

10. **Show the result** to the user for review. Highlight each section.

// turbo
11. **Validate** — run `nodus validate <file>` to confirm correctness.

12. **Report** — if clean, congratulate. If issues, fix them and re-validate.
