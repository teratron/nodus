---
description: Initialize NODUS development environment — create junctions and symlinks for .claude and .agents.
---

# /nodus.dev.init (Initialize Developer Environment)

This workflow initializes the developer environment by linking canonical sources (in `packages/`) to agent-facing interfaces (`.claude/` and `.agents/`). 

It leverages the **nodus-dev-init** skill to perform the platform-specific linking procedures.

## Steps

### 1. Identify Environment
Identify the operating system (Windows vs. Unix) and project root directory.

### 2. Load Nodus Dev Init Skill
Activate the `.agents/skills/nodus-dev-init/` skill. Ensure the following references are available:
- `references/windows.md` (for Windows)
- `references/unix.md` (for Linux/macOS)

### 3. Execute Initialization
// turbo
Follow the platform-appropriate command sequence from the skill's references to establish junctions, hardlinks, and symlinks.

**Windows Tasks:**
- Create `.claude` junctions.
- Link `nodus` skill in `.agents`.
- Create workflow hardlinks.
- Setup core spec junctions for `demo` and `sandbox`.
- Run git index maintenance.

**Unix Tasks:**
- Create `.claude` symlinks.
- Link `nodus` skill in `.agents`.
- Create workflow symlinks.
- Setup core spec symlinks for `demo` and `sandbox`.
- Run git index maintenance.

### 4. Verify Active Links
Run verification commands from the skill and ensure all targets point correctly to project local files. 

---

> [!TIP]
> After running this, Claude and other AI agents will see all workflows and skills from a single source in `packages/` and `.agents/`.
