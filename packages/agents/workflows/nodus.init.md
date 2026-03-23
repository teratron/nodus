---
description: Initialize a new NODUS project in the current directory with guided setup.
---

# /nodus.init

Set up a NODUS project from scratch with guided configuration.

## Steps

// turbo

1. **Check CLI availability** — run `nodus --version`. If the command is not found, stop and tell the user: "The `nodus` CLI is not installed. Run `pip install nodus` and try again."

2. **Check if already initialized.** Look for `.nodus/` directory. If it exists, warn and ask if the user wants to reinitialize.

// turbo
3. **Run init** — execute `nodus init` in the project root.

4. **Configure `config.json`.** Ask the user:

   - Project name (default: current directory name)
   - Preferred model for executor agent (default: `auto`)
   - Enable logging? (default: yes)

5. **Update `.nodus/config.json`** with the user's answers.

6. **Configure `config.nodus`.** Ask:

   - Any global `!!` rules? (e.g. `!!NEVER: publish WITHOUT validate`)
   - Any global `!PREF:` preferences? (e.g. `!PREF: brevity OVER completeness`)

7. **Update `.nodus/config.nodus`** with the rules.

8. **Create initial directories:**

   - `workflows/` — for user workflows
   - `.nodus/context/` — for context files (`brand_voice.md`, etc.)
   - `.nodus/schema/` — for schema extensions

9. **Verify `.gitignore`.** Ensure these entries are present:

   ```
   .nodus/core/
   .nodus/extensions/
   .nodus/.cache/
   ```

10. **Report success:**

    ```
    ✓ NODUS initialized
    ✓ Core schema: .nodus/core/schema.nodus
    ✓ Config: .nodus/config.json
    ✓ Rules: .nodus/config.nodus
    Next: /nodus.create to scaffold your first workflow
    ```

11. **Offer next action:** "Create your first workflow?" → `/nodus.create`
