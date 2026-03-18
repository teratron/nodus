---
description: Initialize a new NODUS project in the current directory with guided setup.
---

# /nodus.init

Set up a NODUS project from scratch with guided configuration.

## Steps

1. **Check if already initialized.** Look for `.nodus/` directory. If it exists, warn and ask if the user wants to reinitialize.

// turbo
2. **Run init** — execute `nodus init` in the project root.

3. **Configure `config.json`.** Ask the user:
   - Project name (default: current directory name)
   - Preferred model for executor agent (default: `claude-sonnet-4`)
   - Enable logging? (default: yes)

4. **Update `.nodus/config.json`** with the user's answers.

5. **Configure `config.nodus`.** Ask:
   - Any global `!!` rules? (e.g. `!!NEVER: publish WITHOUT validate`)
   - Any global `!PREF:` preferences? (e.g. `!PREF: brevity OVER completeness`)

6. **Update `.nodus/config.nodus`** with the rules.

7. **Create initial directories:**
   - `workflows/` — for user workflows
   - `.nodus/context/` — for context files (`brand_voice.md`, etc.)
   - `.nodus/schema/` — for schema extensions

8. **Verify `.gitignore`.** Ensure these entries are present:
   ```
   .nodus/core/
   .nodus/extensions/
   .nodus/.cache/
   ```

9. **Report success:**
   ```
   ✓ NODUS initialized
   ✓ Core schema: .nodus/core/schema.nodus
   ✓ Config: .nodus/config.json
   ✓ Rules: .nodus/config.nodus
   Next: /nodus.create to scaffold your first workflow
   ```

10. **Offer next action:** "Create your first workflow?" → `/nodus.create`
