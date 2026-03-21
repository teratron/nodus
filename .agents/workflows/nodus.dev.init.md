---
description: Initialize NODUS development environment with symbolic links for .claude and package core specs (Windows & Linux).
---

# /nodus.dev.init (Initialize Developer Symlinks)

This workflow automates the creation of symbolic links to avoid file duplication and maintain a single source of truth for Claude configuration and NODUS core schemas across different operating systems.

> [!NOTE]
> The workflow will automatically detect your OS and use `ln -s` on Linux/macOS or `mklink` on Windows.
> The link `.claude/commands/nodus.dev.init.md` 🔗 `.agents/workflows/nodus.dev.init.md` provides direct access to this initialization command.

## 1. Operating System Detection

// turbo
1. Check the operating system:

```bash
python3 -c "import platform; print(platform.system())"
```

## [WINDOWS ONLY] - Using Directory Junctions

If the OS is **Windows**, follow these steps:

// turbo
1. Cleanup and link `.claude` config files:

```powershell
cmd /c "if exist .claude\workflows del /q .claude\workflows & mklink /D .claude\workflows ..\.agents\workflows"
cmd /c "if exist .claude\skills del /q .claude\skills & mklink /D .claude\skills ..\.agents\skills"
cmd /c "if exist .claude\rules del /q .claude\rules & mklink /D .claude\rules ..\.agents\rules"
```

// turbo
2. Setup package core and assistant links:

```powershell
# Core Spec links
cmd /c "if not exist demo\.nodus mkdir demo\.nodus & if exist demo\.nodus\core rmdir /q demo\.nodus\core & mklink /D demo\.nodus\core ..\..\packages\spec\core"
cmd /c "if not exist sandbox\my-project\.nodus mkdir sandbox\my-project\.nodus & if exist sandbox\my-project\.nodus\core rmdir /q sandbox\my-project\.nodus\core & mklink /D sandbox\my-project\.nodus\core ..\..\..\packages\spec\core"

# Assistant Skill (nodus)
cmd /c "if exist .agents\skills\nodus rmdir /q .agents\skills\nodus & mklink /D .agents\skills\nodus ..\..\packages\skills\nodus"

# Universal Assistant Skills (links in .claude to .agents)
cmd /c "cd .claude\skills & for /F \"tokens=*\" %G in ('dir ..\..\.agents\skills /AD /B') do (if NOT \"%G\"==\"nodus\" (if exist %G rmdir /s /q %G & mklink /D %G ..\..\.agents\skills\%G))"

# Assistant Workflows (links to canonical sources in packages/)
cmd /c "cd .agents\workflows & mklink nodus.compile.md ..\..\packages\workflows\nodus.compile.md"
cmd /c "cd .agents\workflows & mklink nodus.create.md ..\..\packages\workflows\nodus.create.md"
cmd /c "cd .agents\workflows & mklink nodus.explain.md ..\..\packages\workflows\nodus.explain.md"
cmd /c "cd .agents\workflows & mklink nodus.init.md ..\..\packages\workflows\nodus.init.md"
cmd /c "cd .agents\workflows & mklink nodus.pack.md ..\..\packages\workflows\nodus.pack.md"
cmd /c "cd .agents\workflows & mklink nodus.run.md ..\..\packages\workflows\nodus.run.md"
cmd /c "cd .agents\workflows & mklink nodus.test.md ..\..\packages\workflows\nodus.test.md"
cmd /c "cd .agents\workflows & mklink nodus.validate.md ..\..\packages\workflows\nodus.validate.md"

# Project-specific commands
cmd /c "if not exist .claude\commands mkdir .claude\commands & cd .claude\commands & if exist nodus.dev.init.md del /q nodus.dev.init.md & mklink nodus.dev.init.md ..\..\.agents\workflows\nodus.dev.init.md"

# Git Index Maintenance (prevent 'beyond a symbolic link' errors)
# This clears the cached files from folders replaced by symlinks
git rm -r --cached .agents/workflows .agents/skills/nodus .claude/workflows .claude/skills .claude/rules .claude/commands demo/.nodus/core sandbox/my-project/.nodus/core
```

## [LINUX / macOS ONLY] - Using Symbolic Links

If the OS is **Linux** or **Darwin**, follow these steps:

// turbo
1. Cleanup and link `.claude` config files:

```bash
rm -f .claude/workflows .claude/skills .claude/rules
ln -s ../.agents/workflows .claude/workflows
ln -s ../.agents/skills .claude/skills
ln -s ../.agents/rules .claude/rules
```

// turbo
2. Setup package core and assistant links:

```bash
# Core Spec and Assistant links
mkdir -p demo/.nodus sandbox/my-project/.nodus
rm -rf demo/.nodus/core sandbox/my-project/.nodus/core .agents/skills/nodus
ln -s ../../packages/spec/core demo/.nodus/core
ln -s ../../../packages/spec/core sandbox/my-project/.nodus/core
ln -s ../../packages/skills/nodus .agents/skills/nodus

# Universal Assistant Skills
for d in .agents/skills/*/; do
  skill=$(basename "$d")
  if [ "$skill" != "nodus" ]; then
    rm -rf ".claude/skills/$skill"
    ln -s "../../.agents/skills/$skill" ".claude/skills/$skill"
  fi
done

# Assistant Workflows
for f in compile create explain init pack run test validate; do
  rm -f .agents/workflows/nodus.$f.md
  ln -s ../../packages/workflows/nodus.$f.md .agents/workflows/nodus.$f.md
done

# Project-specific commands
mkdir -p .claude/commands
rm -f .claude/commands/nodus.dev.init.md
ln -s ../../.agents/workflows/nodus.dev.init.md .claude/commands/nodus.dev.init.md

# Git Index Maintenance (prevent 'beyond a symbolic link' errors)
git rm -r --cached .agents/workflows .agents/skills/nodus .claude/workflows .claude/skills .claude/rules .claude/commands demo/.nodus/core sandbox/my-project/.nodus/core
```

## Verification

// turbo
1. Check that symlinks are active:

```bash
ls -ld .claude/workflows demo/.nodus/core .agents/skills/nodus .claude/commands/nodus.dev.init.md .claude/skills/brainstorming
```

---

> [!TIP]
> After running this, Claude Desktop and other agents will see all workflows, skills, and rules from a single source in `packages/`.
