"""NODUS Constants — language-defining static values."""

from __future__ import annotations

__version__ = "0.4.1"

# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM COMMANDS & KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════

KNOWN_COMMANDS = {
    "FETCH",
    "STORE",
    "LOAD",
    "APPEND",
    "MERGE",
    "ANALYZE",
    "SCORE",
    "COMPARE",
    "GEN",
    "REFINE",
    "TRANSLATE",
    "SUMMARIZE",
    "VALIDATE",
    "ROUTE",
    "ESCALATE",
    "NOTIFY",
    "PUBLISH",
    "QUERY_KB",
    "REMEMBER",
    "RECALL",
    "FORGET",
    "LOG",
    "WAIT",
    "TONE",
    "DEBUG",
    "WRITE",
    "MKDIR",
    "FILE_EXISTS",
    "FILL",
    "PARSE",
    "EXECUTE",
    "SIMULATE",
    "EXTRACT",
    "FILTER",
    "EXECUTE_TEST",
    "READ_FILE",
    "SCAN_DIR",
    "ENV",
    "DATE",
    "COUNTER",
    "GIT",
    "QUERY_GIT",
    "MOVE",
    "COPY",
    "TRANSPILE",
    "HASH",
    "PARSE_MD_HEADER",
    "PARSE_INDEX",
    "VERSION_BUMP",
    "GENERATE_DOC",
}

VALID_TONES = {
    "warm",
    "neutral",
    "formal",
    "casual",
    "urgent",
    "empathetic",
    "brand",
}

RESERVED_VARIABLES = {
    "$in",
    "$out",
    "$error",
    "$meta",
    "$raw",
    "$draft",
    "$ctx",
    "$user",
    "$session",
    "$log",
    "$flags",
    "$quality",
    "$sentiment",
    "$confidence",
    "$memory",
    "$kb_results",
}

# ═══════════════════════════════════════════════════════════════════════════
# ERROR CODES
# ═══════════════════════════════════════════════════════════════════════════

ERR_RULE_VIOLATION = "NODUS:RULE_VIOLATION"
ERR_PARSE_ERROR = "NODUS:PARSE_ERROR"
ERR_MAX_REACHED = "NODUS:MAX_REACHED"
ERR_EXECUTION_FAILED = "NODUS:EXECUTION_FAILED"

# ═══════════════════════════════════════════════════════════════════════════
# TRANSPILER MAPPINGS
# ═══════════════════════════════════════════════════════════════════════════

TRANSPILER_VERB_MAP: dict[str, str] = {
    "FETCH": "Fetch",
    "ANALYZE": "Analyze",
    "GEN": "Generate",
    "VALIDATE": "Validate",
    "ROUTE": "Route to",
    "ESCALATE": "Escalate to",
    "LOG": "Log",
    "PUBLISH": "Publish",
    "NOTIFY": "Notify",
    "REFINE": "Refine",
    "TONE": "Set tone to",
    "REMEMBER": "Store in memory:",
    "RECALL": "Load from memory:",
    "QUERY_KB": "Search knowledge base for",
    "RUN": "Run macro",
}
