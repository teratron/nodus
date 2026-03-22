# ═══════════════════════════════════════════════════════════════════════════════
# NODUS DEV INIT (WINDOWS)
# ═══════════════════════════════════════════════════════════════════════════════

# Safe junction/hardlink creation for Windows environment.
# Note: Junctions (/J) work without admin or Developer Mode.
# Hardlinks (/H) also work without admin for files.

# ───────────────────────────────────────────────────────────────────────────────
# 1. Configuration
# ───────────────────────────────────────────────────────────────────────────────

$workflows = @("compile", "create", "explain", "init", "pack", "run", "test", "validate")
$specs = @(
    @{ Path = "demo\.nodus\core"; Target = "packages\spec\core" },
    @{ Path = "sandbox\my-project\.nodus\core"; Target = "packages\spec\core" }
)

# ───────────────────────────────────────────────────────────────────────────────
# 2. Cleanup function
# ───────────────────────────────────────────────────────────────────────────────

function Remove-Existing($path) {
    if (Test-Path $path) {
        Write-Host "Removing: $path" -ForegroundColor Yellow
        if ((Get-Item $path).Attributes -match "ReparsePoint") {
            # It's a junction or symlink
            if ((Get-Item $path).PSIsContainer) { cmd /c "rmdir $path" } else { cmd /c "del $path" }
        } else {
            # Regular file/directory
            Remove-Item -Recurse -Force $path
        }
    }
}

# ───────────────────────────────────────────────────────────────────────────────
# 3. Main Execution
# ───────────────────────────────────────────────────────────────────────────────

Write-Host ">>> Initializing Windows Agent Environment..." -ForegroundColor Cyan

# 3.1. .claude junctions
Remove-Existing ".claude\commands"
Remove-Existing ".claude\skills"
Remove-Existing ".claude\rules"
cmd /c "mklink /J .claude\commands .agents\workflows"
cmd /c "mklink /J .claude\skills .agents\skills"
cmd /c "mklink /J .claude\rules .agents\rules"

# 3.2. .agents junctions
Remove-Existing ".agents\skills\nodus"
cmd /c "mklink /J .agents\skills\nodus packages\agents\skills\nodus"

# 3.3. Workflow hardlinks
Write-Host "Creating workflow hardlinks..." -ForegroundColor Cyan
foreach ($f in $workflows) {
    $name = "nodus.$f.md"
    $target = "packages\agents\workflows\$name"
    $link = ".agents\workflows\$name"
    Remove-Existing $link
    cmd /c "mklink /H $link $target"
}

# 3.4. Core spec junctions
Write-Host "Linking core specs to demo/sandbox..." -ForegroundColor Cyan
foreach ($s in $specs) {
    $parent = Split-Path $s.Path
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force }
    Remove-Existing $s.Path
    cmd /c "mklink /J $($s.Path) $($s.Target)"
}

# 3.5. Git Index Maintenance
Write-Host "Synchronizing git index..." -ForegroundColor Cyan
$linksToRemove = @(
    ".agents\skills\nodus",
    ".claude\commands",
    ".claude\skills",
    ".claude\rules",
    "demo\.nodus\core",
    "sandbox\my-project\.nodus\core"
)
foreach ($f in $workflows) { $linksToRemove += ".agents\workflows\nodus.$f.md" }

git rm -r --cached --ignore-unmatch $linksToRemove

Write-Host "`n>>> Verification:" -ForegroundColor Green
cmd /c "dir .claude\commands .claude\skills .claude\rules .agents\skills\nodus demo\.nodus\core sandbox\my-project\.nodus\core /AL"
