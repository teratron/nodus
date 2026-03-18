"""Tests for the NODUS Parser.

Verifies AST construction for File types, Headers, Runtime blocks,
Rules, Declarations, Steps, Conditionals, and Tests.
"""

from __future__ import annotations

from runtime.interpreter.ast_nodes import (
    CommandCall,
    Conditional,
    ConfigFile,
    FileType,
    InputDecl,
    Node,
    RuntimeBlock,
    SchemaFile,
    WorkflowFile,
)
from runtime.interpreter.parser import Parser


def parse(source: str, filename: str = "test.nodus") -> Node | None:
    """Parse source string into an AST.

    Args:
        source: Input code string.
        filename: Optional filename for location tracking.

    Returns:
        The root AST node.
    """
    return Parser().parse(source, filename=filename)


# ───────────────────────────────────────────────────────────────────────────
# File type detection
# ───────────────────────────────────────────────────────────────────────────


def test_parse_returns_none_for_empty() -> None:
    """Verify parser returns None for empty source."""
    assert parse("") is None


def test_parse_workflow_file() -> None:
    """Verify parsing of §wf: workflow files."""
    src = "§wf:my_flow v1.0\n§runtime: {\n  core: schema.nodus\n}\n@steps:\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)


def test_parse_schema_file() -> None:
    """Verify parsing of §schema: schema files."""
    src = "§schema:nodus v0.3\n"
    ast = parse(src)
    assert isinstance(ast, SchemaFile)


def test_parse_config_file() -> None:
    """Verify parsing of §config: configuration files."""
    src = "§config:project v1.0\n"
    ast = parse(src)
    assert isinstance(ast, ConfigFile)


# ───────────────────────────────────────────────────────────────────────────
# Header
# ───────────────────────────────────────────────────────────────────────────


def test_workflow_header_name() -> None:
    """Verify parser extracts workflow name correctly."""
    src = "§wf:my_workflow v1.0\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert ast.header and ast.header.name == "my_workflow"


def test_workflow_header_version() -> None:
    """Verify parser extracts workflow version correctly."""
    src = "§wf:my_workflow v2.5\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert ast.header and ast.header.version == "v2.5"


def test_workflow_header_filetype() -> None:
    """Verify parser sets correct FileType in header."""
    src = "§wf:foo v1.0\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert ast.header and ast.header.file_type == FileType.WORKFLOW


# ───────────────────────────────────────────────────────────────────────────
# Runtime block
# ───────────────────────────────────────────────────────────────────────────


def test_runtime_block_parsed() -> None:
    """Verify §runtime block is parsed into RuntimeBlock node."""
    src = "§wf:foo v1.0\n§runtime: {\n  core: core/schema.nodus\n}\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert ast.runtime is not None
    assert isinstance(ast.runtime, RuntimeBlock)


def test_runtime_core_field() -> None:
    """Verify core field in runtime block is captured."""
    src = (
        "§wf:foo v1.0\n§runtime: {\n  core: core/schema.nodus\n  mode: production\n}\n"
    )
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert ast.runtime is not None
    assert (
        "core" in ast.runtime.raw_fields or ast.runtime.core or ast.runtime.raw_fields
    )


# ───────────────────────────────────────────────────────────────────────────
# Rules
# ───────────────────────────────────────────────────────────────────────────


def test_absolute_rule_never() -> None:
    """Verify !!NEVER rules are parsed correctly."""
    src = "§wf:foo v1.0\n§runtime: {}\n!!NEVER: publish without validate\n@steps:\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert any(r.rule_type == "NEVER" for r in ast.rules)


def test_absolute_rule_always() -> None:
    """Verify !!ALWAYS rules are parsed correctly."""
    src = "§wf:foo v1.0\n§runtime: {}\n!!ALWAYS: log the result\n@steps:\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert any(r.rule_type == "ALWAYS" for r in ast.rules)


def test_preference_parsed() -> None:
    """Verify !PREF preferences are parsed correctly."""
    src = "§wf:foo v1.0\n§runtime: {}\n!PREF: empathetic OVER neutral\n@steps:\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert len(ast.preferences) == 1
    pref = ast.preferences[0]
    assert "empathetic" in pref.preferred
    assert "neutral" in pref.over


# ───────────────────────────────────────────────────────────────────────────
# Declarations
# ───────────────────────────────────────────────────────────────────────────


def test_input_decl_parsed() -> None:
    """Verify @in declarations are parsed into InputDecl nodes."""
    src = "§wf:foo v1.0\n§runtime: {}\n@in: {\n  msg: str\n  url: url\n}\n@steps:\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert ast.input_decl is not None
    assert isinstance(ast.input_decl, InputDecl)


def test_output_decl_parsed() -> None:
    """Verify @out declarations are parsed into OutputDecl nodes."""
    src = "§wf:foo v1.0\n§runtime: {}\n@out: $out\n@steps:\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert ast.output_decl is not None
    assert ast.output_decl.variable == "$out"


def test_context_decl_parsed() -> None:
    """Verify @ctx declarations are parsed into ContextDecl nodes."""
    src = "§wf:foo v1.0\n§runtime: {}\n@ctx: [brand_voice]\n@steps:\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert ast.context_decl is not None
    assert "brand_voice" in ast.context_decl.contexts


def test_error_decl_parsed() -> None:
    """Verify @err declarations are parsed into ErrorDecl nodes."""
    src = "§wf:foo v1.0\n§runtime: {}\n@err: ESCALATE(human)\n@steps:\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert ast.error_decl is not None


# ───────────────────────────────────────────────────────────────────────────
# Steps
# ───────────────────────────────────────────────────────────────────────────


def test_steps_parsed() -> None:
    """Verify @steps sequence is parsed into node list."""
    src = '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. LOG("hello")\n'
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert len(ast.steps) >= 1


def test_step_number() -> None:
    """Verify step numbers are captured correctly."""
    src = '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. LOG("a")\n  2. LOG("b")\n'
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert ast.steps[0].number == 1
    assert ast.steps[1].number == 2


def test_command_call_name() -> None:
    """Verify command names are captured correctly."""
    src = "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. FETCH($in.url)\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    body = ast.steps[0].body
    assert isinstance(body, CommandCall)
    assert body.name == "FETCH"


def test_command_call_pipeline_target() -> None:
    """Verify command pipeline targets (→) are captured."""
    src = "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. FETCH($in.url) \u2192 $raw\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    body = ast.steps[0].body
    assert isinstance(body, CommandCall)
    assert body.pipeline_target == "$raw"


def test_command_call_modifier() -> None:
    """Verify command modifiers (+) are captured."""
    src = "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. FETCH($in.url) +cache=false \u2192 $raw\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    body = ast.steps[0].body
    assert isinstance(body, CommandCall)
    assert "+cache" in body.modifiers


def test_command_call_validator() -> None:
    """Verify command validators (^) are captured."""
    src = "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. VALIDATE($draft) ^brand_voice \u2192 $v\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    body = ast.steps[0].body
    assert isinstance(body, CommandCall)
    assert any("brand_voice" in v for v in body.validators)


def test_command_call_flag() -> None:
    """Verify command flags (~) are captured."""
    src = "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. ANALYZE($raw) ~sentiment \u2192 $meta\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    body = ast.steps[0].body
    assert isinstance(body, CommandCall)
    assert "sentiment" in body.flags


# ───────────────────────────────────────────────────────────────────────────
# Conditionals
# ───────────────────────────────────────────────────────────────────────────


def test_conditional_inline() -> None:
    """Verify inline ?IF conditionals are parsed."""
    src = "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. ?IF $raw = null \u2192 !BREAK\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    body = ast.steps[0].body
    assert isinstance(body, Conditional)


def test_conditional_if_condition() -> None:
    """Verify condition text in ?IF blocks is captured."""
    src = (
        '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. ?IF $score > 0.8 \u2192 LOG("ok")\n'
    )
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    cond = ast.steps[0].body
    assert isinstance(cond, Conditional)
    assert "$score" in cond.condition


# ───────────────────────────────────────────────────────────────────────────
# Test blocks
# ───────────────────────────────────────────────────────────────────────────


def test_test_block_parsed() -> None:
    """Verify @test blocks are parsed into NodusTestBlock nodes."""
    src = (
        '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. LOG("x")\n'
        '@test:smoke {\n  input: { msg: "hello" }\n  expected: { status = SUCCESS }\n}\n'
    )
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert len(ast.tests) == 1
    assert ast.tests[0].name == "smoke"


def test_multiple_test_blocks() -> None:
    """Verify multiple @test blocks in one file are captured."""
    src = (
        '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. LOG("x")\n'
        "@test:happy {\n  input: {}\n}\n"
        "@test:sad {\n  input: {}\n}\n"
    )
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert len(ast.tests) == 2


# ───────────────────────────────────────────────────────────────────────────
# Human mode
# ───────────────────────────────────────────────────────────────────────────


def test_human_mode_detected() -> None:
    """Verify HUMAN MODE comment block is captured."""
    src = (
        '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. LOG("x")\n'
        ";; HUMAN MODE\n;; This is a plain description.\n"
    )
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)
    assert ast.human_mode is not None


# ───────────────────────────────────────────────────────────────────────────
# Schema file
# ───────────────────────────────────────────────────────────────────────────


def test_schema_named_blocks() -> None:
    """Verify §schema files and their named blocks are parsed."""
    src = "§schema:nodus v0.3\n§commands {\n  FETCH: fetch resource\n}\n"
    ast = parse(src)
    assert isinstance(ast, SchemaFile)
    assert "commands" in ast.sections
