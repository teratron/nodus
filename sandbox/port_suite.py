"""
port_suite.py
Adapts sandbox/before/tests/suite.md from Magic SDD vocabulary to NODUS.

Replacements applied (in order):
  1. Template paths           (.magic/templates/X  ->  .nodus/templates/X)
  2. Agent workflow paths     (.agent/workflows/magic.X.md  ->  .nodus/workflows/sdd/X.nodus)
  3. CLI trigger syntax       /magic.X  ->  sdd X
  4. Script invocations       node .magic/scripts/executor.js X  ->  RUN(wf:sdd.X)
  5. check-prerequisites      ->  CHECK_PREREQS()
  6. update-engine-meta       ->  UPDATE_ENGINE_META()
  7. Generic .magic/ paths    ->  .nodus/
  8. Workflow file refs        X.md  ->  wf:sdd.X  (known names only, backtick then bare)
  9. Product / brand names     Magic SDD, magic-spec

Note: template paths must be replaced BEFORE workflow bare refs to avoid
      retrospective.md -> wf:sdd.retro mangling inside template paths.
"""

import re
from pathlib import Path

SRC = Path(__file__).parent / "before" / "tests" / "suite.md"
DST = Path(__file__).parent / "after" / ".nodus" / "tests" / "suite.md"

# Workflow name map: file base -> NODUS alias
WF_NAMES = [
    ("retrospective", "retro"),
    ("simulate",      "simulate"),
    ("analyze",       "analyze"),
    ("init",          "init"),
    ("spec",          "spec"),
    ("task",          "task"),
    ("run",           "run"),
    ("rule",          "rule"),
]

# ── Ordered replacement rules ──────────────────────────────────────────────
# Each entry: (pattern, replacement, use_regex)
RULES: list[tuple[str, str, bool]] = [

    # ── 1. Template paths (must run before workflow bare refs) ─────────────
    # Specific retrospective template -> retro.md  (before generic rule)
    (
        ".magic/templates/retrospective.md",
        ".nodus/templates/retro.md",
        False,
    ),
    # Generic template paths
    (
        r"\.magic/templates/([\w-]+)\.md",
        r".nodus/templates/\1.md",
        True,
    ),

    # ── 2. Agent workflow paths ────────────────────────────────────────────
    (
        r"\.agent/workflows/magic\.(\w+)\.md",
        r".nodus/workflows/sdd/\1.nodus",
        True,
    ),

    # ── 3. CLI triggers (/magic.X and magic.X -> sdd X) ──────────────────
    (r"`/magic\.(\w+)`",  r"`sdd \1`", True),
    (r"/magic\.(\w+)",    r"sdd \1",   True),
    # bare magic.X (no leading slash) in backticks and prose
    (r"`magic\.(\w+)`",   r"`sdd \1`", True),
    (r"\bmagic\.(\w+)\b", r"sdd \1",   True),

    # ── 4. node executor invocations ──────────────────────────────────────
    (
        r"node \.magic/scripts/executor\.js (\w+)",
        r"RUN(wf:sdd.\1)",
        True,
    ),

    # ── 5. check-prerequisites ────────────────────────────────────────────
    (
        r"check-prerequisites → ok: false",
        "CHECK_PREREQS() -> { ok: false }",
        False,
    ),
    (
        r"check-prerequisites → ok\b",
        "CHECK_PREREQS() -> { ok: true }",
        False,
    ),
    # Bare check-prerequisites (regex for word boundary)
    (
        r"check-prerequisites\b",
        "CHECK_PREREQS()",
        True,
    ),

    # ── 6. update-engine-meta ─────────────────────────────────────────────
    (
        r"update-engine-meta --workflow ([\w{}\-]+)",
        r"UPDATE_ENGINE_META() +workflow=\1",
        True,
    ),
    (r"`update-engine-meta`", "`UPDATE_ENGINE_META()`", False),

    # ── 6b. executor.js references ────────────────────────────────────────
    # In workflow context lines it's a command ref -> replace with NODUS equivalent
    (r"`executor\.js`",            "`CHECK_PREREQS()`",   False),
    # In prose/test expected: keep contextual but rename
    (
        r"\bexecutor\.js\b",
        "nodus-runtime",
        True,
    ),

    # ── 7. Generic .magic/ paths ──────────────────────────────────────────
    (r"\.magic/", ".nodus/", True),

    # ── 8. Workflow file refs: backtick variants (retrospective first) ─────
    *[
        (rf"`{name}\.md`", f"`wf:sdd.{alias}`", True)
        for name, alias in WF_NAMES
    ],
    # Bare workflow refs in prose (e.g. "Workflow: init.md")
    *[
        (rf"\b{name}\.md\b", f"wf:sdd.{alias}", True)
        for name, alias in WF_NAMES
    ],

    # ── 9. Product / brand names ──────────────────────────────────────────
    ("magic-spec", "nodus",     False),
    ("Magic SDD",  "NODUS SDD", False),
    # dot-prefixed command aliases still in text after CLI trigger replacement
    ("sdd spec",     "sdd spec",  False),   # no-op, just documents intent
]


def apply_rules(text: str) -> str:
    for pattern, replacement, use_regex in RULES:
        if use_regex:
            text = re.sub(pattern, replacement, text)
        else:
            text = text.replace(pattern, replacement)
    return text


def update_header(text: str) -> str:
    """Replace first-line metadata and prepend migration note."""
    text = text.replace(
        "**Version:** 1.9.45\n",
        "**Version:** 1.9.45 (ported to NODUS)\n",
    )
    text = text.replace(
        "Regression testing for Magic SDD engine workflows.",
        "Regression testing for NODUS SDD engine workflows.",
    )
    text = text.replace(
        "**Trigger:** `/magic.simulate test`",
        "**Trigger:** `sdd simulate test`",
    )
    text = text.replace(
        "`.magic/*.md`",
        "`.nodus/workflows/sdd/*.nodus`",
    )
    note = (
        ";; Ported from sandbox/before/tests/suite.md (Magic SDD v1.9.45)\n"
        ";; Vocabulary adapted to NODUS. Test logic and T-IDs unchanged.\n"
        ";; TODO: verify mock values against current .nodus workflow implementations.\n"
    )
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            lines.insert(i + 1, note)
            break
    return "\n".join(lines)


def main() -> None:
    src_text = SRC.read_text(encoding="utf-8")

    # Header substitutions run first (before apply_rules to avoid cascading)
    result = update_header(src_text)
    result = apply_rules(result)

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(result, encoding="utf-8")

    # Validation stats
    old_count = src_text.count("### T")
    new_count = result.count("### T")
    magic_remaining = (
        result.count(".magic/")
        + result.count("/magic.")
        + result.count("executor.js")
        + result.lower().count("magic sdd")
    )
    prereqs_remaining = result.count("check-prerequisites")

    print(f"Source : {SRC}")
    print(f"Output : {DST}")
    print(f"Tests  : {old_count} -> {new_count} (must be equal)")
    print(f".magic / magic. refs remaining : {magic_remaining} (should be 0)")
    print(f"check-prerequisites remaining  : {prereqs_remaining} (should be 0)")


if __name__ == "__main__":
    main()
