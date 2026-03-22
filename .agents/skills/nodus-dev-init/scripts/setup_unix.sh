#!/usr/bin/env bash

# ───────────────────────────────────────────────────────────────────────────────
# NODUS DEV INIT (UNIX)
# ───────────────────────────────────────────────────────────────────────────────

set -e

echo ">>> Initializing Unix/macOS Agent Environment..."

# 1. Create .claude symlinks
mkdir -p .claude
rm -rf .claude/commands .claude/skills .claude/rules
ln -s ../.agents/workflows .claude/commands
ln -s ../.agents/skills .claude/skills
ln -s ../.agents/rules .claude/rules

# 2. Global Agent Instructions (Linking to AGENTS.md)
echo "Linking agent instruction files..."
agentFiles="CLAUDE.md QWEN.md"
for f in $agentFiles; do
  rm -f $f
  ln -s AGENTS.md $f
done

# 3. Setup .agents symlinks (nodus skill)
mkdir -p .agents/skills .agents/workflows .agents/rules
rm -rf .agents/skills/nodus
ln -s ../../packages/agents/skills/nodus .agents/skills/nodus

# 4. Workflow symlinks
echo "Creating workflow symlinks..."
for f in compile create explain init pack run test validate; do
  rm -f .agents/workflows/nodus.$f.md
  ln -s ../../packages/agents/workflows/nodus.$f.md .agents/workflows/nodus.$f.md
done

# 5. Project Core Specs
echo "Linking core specs to project environments (demo, sandbox)..."
mkdir -p demo/.nodus sandbox/my-project/.nodus
rm -rf demo/.nodus/core sandbox/my-project/.nodus/core
ln -s ../../packages/spec/core demo/.nodus/core
ln -s ../../../packages/spec/core sandbox/my-project/.nodus/core

# 6. Git Maintenance
echo "Synchronizing git index..."
links=".agents/skills/nodus .claude/commands .claude/skills .claude/rules demo/.nodus/core sandbox/my-project/.nodus/core"
for f in compile create explain init pack run test validate; do
  links="$links .agents/workflows/nodus.$f.md"
done
for f in $agentFiles; do
  links="$links $f"
done
git rm -r --cached --ignore-unmatch $links

echo -e "\n>>> Verification:"
verifyLinks=".claude/commands .claude/skills .claude/rules .agents/skills/nodus demo/.nodus/core sandbox/my-project/.nodus/core"
for f in $agentFiles; do
  verifyLinks="$verifyLinks $f"
done
for f in compile create explain init pack run test validate; do
  verifyLinks="$verifyLinks .agents/workflows/nodus.$f.md"
done
ls -ld $verifyLinks
