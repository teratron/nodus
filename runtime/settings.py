"""NODUS Settings — default configurations and presets."""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════
# DEFAULT PATHS & CONFIG
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_CONFIG_PATH = ".nodus/config.json"
DEFAULT_SCHEMA_PATH = "core/schema.nodus"

DEFAULT_CONFIG_DATA = {
    "version": "0.1",
    "project": "unnamed",
    "schema": {"core": ".nodus/core/schema.nodus", "extends": []},
    "agents": {
        "executor": {
            "model": "claude-sonnet-4",
            "context_files": [".nodus/core/AGENTS.md"],
        }
    },
    "logging": {"enabled": True, "output": "./logs"},
}

# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════

NEW_WORKFLOW_TEMPLATE = """§wf:{stem} v0.1

§runtime: {
  core:    .nodus/core/schema.nodus
  mode:    NODUS
}

@in: { }
@out: $out

@steps:
  1. ;; TODO: define workflow steps

@err: ESCALATE("human")
"""

NEW_CONFIG_NODUS_TEMPLATE = """§config:{project} v1.0
;; Project Config — Business Logic Layer
;; Purpose:  Global rules, triggers, and constants for all workflows.
;;           This file is loaded by the executor agent at project startup.
;;           It defines WHAT the project does — not WHERE it runs.
;;           For infrastructure (API keys, models, webhooks) → .nodus/config.json

§runtime: {{
  core:    .nodus/core/schema.nodus
  mode:    production
}}

;; ─────────────────────────────────────────────
;; GLOBAL ABSOLUTE RULES
;; ─────────────────────────────────────────────

!!NEVER:  publish WITHOUT validate
!!NEVER:  skip LOG($out)
!!ALWAYS: return NODUS:RESULT on completion or failure
!!ALWAYS: ESCALATE(human) IF $error.level = critical

;; ─────────────────────────────────────────────
;; GLOBAL PREFERENCES
;; ─────────────────────────────────────────────

!PREF: tone = brand OVER tone = neutral

;; ─────────────────────────────────────────────
;; END §config:{project} v1.0
;; ─────────────────────────────────────────────
"""

# ═══════════════════════════════════════════════════════════════════════════
# EXECUTOR & AGENT DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════

AGENT_ID = "nodus-executor"
DEFAULT_UNTIL_ITERATIONS = 5

# ═══════════════════════════════════════════════════════════════════════════
# STUBS & MOCKS (TESTING)
# ═══════════════════════════════════════════════════════════════════════════

STUB_GENERATE_TEMPLATE = "[Generated {prompt} in {tone} tone (STUB)]"
STUB_ANALYZE_VALUE = "mock_value"
STUB_ANALYZE_SCORE = 0.5
STUB_REFINE_TEXT = "[Refined content]"
STUB_TRANSLATE_TEXT = "[Translated content]"
STUB_SUMMARIZE_TEXT = "[Summary]"
STUB_SCORE_VALUE = 0.85

# ═══════════════════════════════════════════════════════════════════════════
# UI STRINGS
# ═══════════════════════════════════════════════════════════════════════════

CLI_HELP = """NODUS CLI — command-line interface for the NODUS language runtime.

Commands:
    nodus validate <file>       Lint/validate a .nodus file
    nodus run <file> [--input]  Execute a workflow
    nodus transpile <file>      Convert between NODUS and HUMAN modes
    nodus test <file>           Run embedded @test blocks
    nodus new <name>            Scaffold a new .nodus workflow
    nodus schema inspect        Show loaded schema summary
    nodus version               Print version info
    nodus help                  Show this help
"""
