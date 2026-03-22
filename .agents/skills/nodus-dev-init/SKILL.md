---
name: nodus-dev-init
description: Initialize NODUS development environment with junctions and symlinks.
---

# NODUS Dev Init Skill

This skill provides the logic and commands to set up the NODUS development environment. It ensures that junctions, hardlinks, and symlinks correctly point to canonical sources in `packages/`.

## Procedures

### 1. Identify Environment

Identify the operating system (Windows vs. Unix/macOS).

### 2. Execute Initialization Script

Establish all junctions and symlinks using the platform-specific script:

**On Windows (PowerShell):**

```powershell
pwsh -NoProfile -File .agents/skills/nodus-dev-init/scripts/setup_windows.ps1
```

**On Unix (Bash):**

```bash
bash .agents/skills/nodus-dev-init/scripts/setup_unix.sh
```

### 3. Verification

Confirm that all links are active and point to correct targets inside the project. Junctions should resolve to absolute paths at the time of creation.

## Resources

- [scripts/setup_windows.ps1](scripts/setup_windows.ps1) - Exact PowerShell/CMD command sequence for Windows.
- [scripts/setup_unix.sh](scripts/setup_unix.sh) - Exact Bash command sequence for Linux/macOS.
