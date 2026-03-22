---
description: Initialize NODUS development environment — create junctions and symlinks for .claude and .agents.
---

# /nodus.dev.init (Initialize Developer Environment)

This workflow creates junctions (Windows) or symlinks (Linux/macOS) so that Claude and other AI agents
see a single source of truth: canonical workflows and skills live in `packages/agents/`, everything else
points there.

```
packages/agents/skills/nodus/   ←─ junction ── .agents/skills/nodus/
packages/agents/workflows/      ←─ hard link (Win) / symlink (Linux) ── .agents/workflows/nodus.*.md
packages/spec/core/             ←─ junction ── demo/.nodus/core
                                               sandbox/my-project/.nodus/core

.agents/skills/   ←─ junction ── .claude/skills/
.agents/workflows/ ←─ junction ── .claude/commands/
```

> [!NOTE]
> The workflow will automatically detect your OS and use `ln -s` on Linux/macOS or `mklink` on Windows.
> `nodus.dev.init.md` itself lives in `.agents/workflows/` and is accessible as `/nodus.dev.init`
> through the `.claude/commands` → `.agents/workflows` junction.

## 1. Operating System Detection

1. Check the operating system:

```bash
python3 -c "import platform; print(platform.system())"
```

## [WINDOWS ONLY] - Using Directory Junctions and Hard Links

If the OS is **Windows**, follow these steps:

> [!NOTE]
> Junctions (`mklink /J`) do not require administrator privileges.
> Hard links (`mklink /H`) do not require administrator privileges and are used for `.md` files
> because Windows file symlinks (`mklink`) require Developer Mode or admin rights.

// turbo

1. Create `.claude` junctions (agent interface):

```powershell
cmd /c "if exist .claude\commands rmdir /s /q .claude\commands & mklink /J .claude\commands .agents\workflows"
cmd /c "if exist .claude\skills rmdir /s /q .claude\skills & mklink /J .claude\skills .agents\skills"
```

// turbo
2. Setup `.agents` links and core spec junctions:

```powershell
# Nodus skill junction (.agents/skills/nodus → packages/agents/skills/nodus)
cmd /c "if exist .agents\skills\nodus rmdir /s /q .agents\skills\nodus & mklink /J .agents\skills\nodus packages\agents\skills\nodus"

# Workflow hard links (.agents/workflows/nodus.*.md → packages/agents/workflows/nodus.*.md)
cmd /c "cd .agents\workflows & if exist nodus.compile.md del /q nodus.compile.md & mklink /H nodus.compile.md ..\..\packages\agents\workflows\nodus.compile.md"
cmd /c "cd .agents\workflows & if exist nodus.create.md del /q nodus.create.md & mklink /H nodus.create.md ..\..\packages\agents\workflows\nodus.create.md"
cmd /c "cd .agents\workflows & if exist nodus.explain.md del /q nodus.explain.md & mklink /H nodus.explain.md ..\..\packages\agents\workflows\nodus.explain.md"
cmd /c "cd .agents\workflows & if exist nodus.init.md del /q nodus.init.md & mklink /H nodus.init.md ..\..\packages\agents\workflows\nodus.init.md"
cmd /c "cd .agents\workflows & if exist nodus.pack.md del /q nodus.pack.md & mklink /H nodus.pack.md ..\..\packages\agents\workflows\nodus.pack.md"
cmd /c "cd .agents\workflows & if exist nodus.run.md del /q nodus.run.md & mklink /H nodus.run.md ..\..\packages\agents\workflows\nodus.run.md"
cmd /c "cd .agents\workflows & if exist nodus.test.md del /q nodus.test.md & mklink /H nodus.test.md ..\..\packages\agents\workflows\nodus.test.md"
cmd /c "cd .agents\workflows & if exist nodus.validate.md del /q nodus.validate.md & mklink /H nodus.validate.md ..\..\packages\agents\workflows\nodus.validate.md"

# Core spec junctions (demo and sandbox projects)
cmd /c "if not exist demo\.nodus mkdir demo\.nodus & if exist demo\.nodus\core rmdir /s /q demo\.nodus\core & mklink /J demo\.nodus\core packages\spec\core"
cmd /c "if not exist sandbox\my-project\.nodus mkdir sandbox\my-project\.nodus & if exist sandbox\my-project\.nodus\core rmdir /s /q sandbox\my-project\.nodus\core & mklink /J sandbox\my-project\.nodus\core packages\spec\core"

# Git index maintenance (prevent 'beyond a symbolic link' errors)
git rm -r --cached --ignore-unmatch .agents/workflows .agents/skills/nodus .claude/commands .claude/skills demo/.nodus/core sandbox/my-project/.nodus/core
```

## [LINUX / macOS ONLY] - Using Symbolic Links

If the OS is **Linux** or **Darwin**, follow these steps:

// turbo

1. Create `.claude` symlinks (agent interface):

```bash
rm -rf .claude/commands .claude/skills
ln -s ../.agents/workflows .claude/commands
ln -s ../.agents/skills .claude/skills
```

// turbo
2. Setup `.agents` links and core spec symlinks:

```bash
# Nodus skill symlink
rm -rf .agents/skills/nodus
ln -s ../../packages/agents/skills/nodus .agents/skills/nodus

# Workflow symlinks (.agents/workflows/nodus.*.md → packages/agents/workflows/)
for f in compile create explain init pack run test validate; do
  rm -f .agents/workflows/nodus.$f.md
  ln -s ../../packages/agents/workflows/nodus.$f.md .agents/workflows/nodus.$f.md
done

# Core spec symlinks (demo and sandbox projects)
mkdir -p demo/.nodus sandbox/my-project/.nodus
rm -rf demo/.nodus/core sandbox/my-project/.nodus/core
ln -s ../../packages/spec/core demo/.nodus/core
ln -s ../../../packages/spec/core sandbox/my-project/.nodus/core

# Git index maintenance (prevent 'beyond a symbolic link' errors)
git rm -r --cached --ignore-unmatch .agents/workflows .agents/skills/nodus .claude/commands .claude/skills demo/.nodus/core sandbox/my-project/.nodus/core
```

## Verification

// turbo

1. Check that all links are active:

**Windows:**

```powershell
dir .claude\commands .claude\skills .agents\skills\nodus demo\.nodus\core /AL
```

**Linux / macOS:**

```bash
ls -ld .claude/commands .claude/skills .agents/skills/nodus demo/.nodus/core
```

---

> After running this, Claude and other AI agents will see all workflows and skills
> from a single source in `packages/` and `.agents/`.
