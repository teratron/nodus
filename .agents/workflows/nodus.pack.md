---
description: Create a new NODUS pack — a shareable bundle of workflows and schema for a specific domain.
---

# /nodus.pack

Guide the user through creating a new NODUS pack from scratch.

## Steps

1. **Ask about the pack:**
   - Domain name (e.g. `social`, `support`, `analytics`) — becomes `nodus-<domain>`
   - Short description
   - Author name

2. **Create the pack directory structure:**
   ```
   packs/nodus-<domain>/
   ├── pack.json
   ├── schema.nodus
   ├── workflows/
   ├── context/
   └── README.md
   ```

3. **Generate `pack.json`** with required fields:
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

4. **Scaffold `schema.nodus`** — domain-specific schema extension with placeholder sections for custom commands, validators, and analysis flags.

5. **Scaffold `README.md`** — pack documentation with install instructions, workflow list, and usage examples.

6. **Ask about workflows.** For each workflow:
   - Name and purpose
   - Trigger type
   - Create using the same flow as `/nodus.create`
   - Add workflow name to `pack.json` `workflows` array

7. **Ask about context files.** Does the pack include example context documents? Create them in `context/`.

// turbo
8. **Validate all workflows** — run `nodus validate packs/nodus-<domain>/workflows/`.

9. **Report the result:**
   ```
   ✓ Pack nodus-<domain> created
   ✓ Workflows: 2
   ✓ Schema: packs/nodus-<domain>/schema.nodus
   ✓ README: packs/nodus-<domain>/README.md
   ```

10. **Offer next actions:**
    - "Add more workflows?" → `/nodus.create`
    - "Test the pack?" → `/nodus.test`
    - "Publish?" → explain pack publishing flow
