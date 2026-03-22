---
description: Create a new NODUS pack — a shareable bundle of workflows and schema for a specific domain.
---

# /nodus.pack

Guide the user through creating a new NODUS pack from scratch.

## Steps

// turbo

1. **Check CLI availability** — run `nodus --version`. If the command is not found, stop and tell the user: "The `nodus` CLI is not installed. Run `pip install nodus` and try again."

2. **Ask about the pack:**
   - Domain name (e.g. `social`, `support`, `analytics`) — becomes `nodus-<domain>`
   - Short description
   - Author name

3. **Create the pack directory structure:**

   ```
   packs/nodus-<domain>/
   ├── pack.json
   ├── schema.nodus
   ├── workflows/
   ├── context/
   └── README.md
   ```

4. **Generate `pack.json`** with required fields:

   ```json
   {
     "name": "nodus-<domain>",
     "version": "1.0.0",
     "description": "<user description>",
     "author": "<user name>",
     "nodus": ">=0.1",
     "workflows": [],
     "keywords": ["<domain>"]
   }
   ```

5. **Scaffold `schema.nodus`** — domain-specific schema extension with placeholder sections for custom commands, validators, and analysis flags.

6. **Scaffold `README.md`** — pack documentation with install instructions, workflow list, and usage examples.

7. **Ask about workflows.** For each workflow the user wants to include, gather the following and create the `.nodus` file:

   - **Name** (`snake_case`) and one-sentence purpose
   - **Trigger** — event (`@ON: event_name`), scheduled (`@ON: schedule:HH:MM`), webhook, or manual
   - **Inputs** — for each field: name, type (`str`, `int`, `float`, `bool`, `list`, `dict`, `enum[...]`), required or optional (with default)
   - **Constraints** — what must `!!NEVER` / `!!ALWAYS` happen
   - **Context files** — any `@ctx:` files needed

   After gathering info, scaffold the file, fill in all sections (`§wf:`, `§runtime:`, `@ON:`, `!!`, `!PREF:`, `@in:`, `@out:`, `@ctx:`, `@err:`, `@steps:`, `;; HUMAN MODE`, `@test:`), and add the workflow name to `pack.json` `workflows` array.

8. **Ask about context files.** Does the pack include example context documents? Create them in `context/`.

// turbo
9. **Validate all workflows** — run `nodus validate packs/nodus-<domain>/workflows/`.

10. **Report the result:**

    ```
    ✓ Pack nodus-<domain> created
    ✓ Workflows: N
    ✓ Schema: packs/nodus-<domain>/schema.nodus
    ✓ README: packs/nodus-<domain>/README.md
    ```

11. **Offer next actions:**
    - "Add more workflows?" → repeat step 7 for a new workflow
    - "Test the pack?" → `/nodus.test`
    - "Publish?" → explain pack publishing flow
