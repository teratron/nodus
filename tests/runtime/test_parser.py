"""Tests for the NODUS Parser."""

from typing import Any

from runtime.interpreter.ast_nodes import (
    CommandCall,
    Conditional,
    ConfigFile,
    FileType,
    InputDecl,
    RuntimeBlock,
    SchemaFile,
    WorkflowFile,
)
from runtime.interpreter.parser import Parser


def parse(source: str, filename: str = "test.nodus") -> Any:
    return Parser().parse(source, filename=filename)


# ── File type detection ─────────────────────────────────────────


def test_parse_returns_none_for_empty():
    assert parse("") is None


def test_parse_workflow_file():
    src = "§wf:my_flow v1.0\n§runtime: {\n  core: schema.nodus\n}\n@steps:\n"
    ast = parse(src)
    assert isinstance(ast, WorkflowFile)


def test_parse_schema_file():
    src = "§schema:nodus v0.3\n"
    ast = parse(src)
    assert isinstance(ast, SchemaFile)


def test_parse_config_file():
    src = "§config:project v1.0\n"
    ast = parse(src)
    assert isinstance(ast, ConfigFile)


# ── Header ──────────────────────────────────────────────────────


def test_workflow_header_name():
    src = "§wf:my_workflow v1.0\n"
    ast = parse(src)
    assert ast.header.name == "my_workflow"


def test_workflow_header_version():
    src = "§wf:my_workflow v2.5\n"
    ast = parse(src)
    assert ast.header.version == "v2.5"


def test_workflow_header_filetype():
    src = "§wf:foo v1.0\n"
    ast = parse(src)
    assert ast.header.file_type == FileType.WORKFLOW


# ── Runtime block ───────────────────────────────────────────────


def test_runtime_block_parsed():
    src = "§wf:foo v1.0\n§runtime: {\n  core: core/schema.nodus\n}\n"
    ast = parse(src)
    assert ast.runtime is not None
    assert isinstance(ast.runtime, RuntimeBlock)


def test_runtime_core_field():
    src = (
        "§wf:foo v1.0\n§runtime: {\n  core: core/schema.nodus\n  mode: production\n}\n"
    )
    ast = parse(src)
    assert (
        "core" in ast.runtime.raw_fields or ast.runtime.core or ast.runtime.raw_fields
    )


# ── Rules ───────────────────────────────────────────────────────


def test_absolute_rule_never():
    src = "§wf:foo v1.0\n§runtime: {}\n!!NEVER: publish without validate\n@steps:\n"
    ast = parse(src)
    assert any(r.rule_type == "NEVER" for r in ast.rules)


def test_absolute_rule_always():
    src = "§wf:foo v1.0\n§runtime: {}\n!!ALWAYS: log the result\n@steps:\n"
    ast = parse(src)
    assert any(r.rule_type == "ALWAYS" for r in ast.rules)


def test_preference_parsed():
    src = "§wf:foo v1.0\n§runtime: {}\n!PREF: empathetic OVER neutral\n@steps:\n"
    ast = parse(src)
    assert len(ast.preferences) == 1
    pref = ast.preferences[0]
    assert "empathetic" in pref.preferred
    assert "neutral" in pref.over


# ── Declarations ────────────────────────────────────────────────


def test_input_decl_parsed():
    src = "§wf:foo v1.0\n§runtime: {}\n@in: {\n  msg: str\n  url: url\n}\n@steps:\n"
    ast = parse(src)
    assert ast.input_decl is not None
    assert isinstance(ast.input_decl, InputDecl)


def test_output_decl_parsed():
    src = "§wf:foo v1.0\n§runtime: {}\n@out: $out\n@steps:\n"
    ast = parse(src)
    assert ast.output_decl is not None
    assert ast.output_decl.variable == "$out"


def test_context_decl_parsed():
    src = "§wf:foo v1.0\n§runtime: {}\n@ctx: [brand_voice]\n@steps:\n"
    ast = parse(src)
    assert ast.context_decl is not None
    assert "brand_voice" in ast.context_decl.contexts


def test_error_decl_parsed():
    src = "§wf:foo v1.0\n§runtime: {}\n@err: ESCALATE(human)\n@steps:\n"
    ast = parse(src)
    assert ast.error_decl is not None


# ── Steps ───────────────────────────────────────────────────────


def test_steps_parsed():
    src = '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. LOG("hello")\n'
    ast = parse(src)
    assert len(ast.steps) >= 1


def test_step_number():
    src = '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. LOG("a")\n  2. LOG("b")\n'
    ast = parse(src)
    assert ast.steps[0].number == 1
    assert ast.steps[1].number == 2


def test_command_call_name():
    src = "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. FETCH($in.url)\n"
    ast = parse(src)
    body = ast.steps[0].body
    assert isinstance(body, CommandCall)
    assert body.name == "FETCH"


def test_command_call_pipeline_target():
    src = "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. FETCH($in.url) → $raw\n"
    ast = parse(src)
    body = ast.steps[0].body
    assert isinstance(body, CommandCall)
    assert body.pipeline_target == "$raw"


def test_command_call_modifier():
    src = (
        "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. FETCH($in.url) +cache=false → $raw\n"
    )
    ast = parse(src)
    body = ast.steps[0].body
    assert isinstance(body, CommandCall)
    assert "+cache" in body.modifiers


def test_command_call_validator():
    src = (
        "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. VALIDATE($draft) ^brand_voice → $v\n"
    )
    ast = parse(src)
    body = ast.steps[0].body
    assert isinstance(body, CommandCall)
    assert any("brand_voice" in v for v in body.validators)


def test_command_call_flag():
    src = "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. ANALYZE($raw) ~sentiment → $meta\n"
    ast = parse(src)
    body = ast.steps[0].body
    assert isinstance(body, CommandCall)
    assert "sentiment" in body.flags


# ── Conditionals ────────────────────────────────────────────────


def test_conditional_inline():
    src = "§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. ?IF $raw = null → !BREAK\n"
    ast = parse(src)
    body = ast.steps[0].body
    assert isinstance(body, Conditional)


def test_conditional_if_condition():
    src = '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. ?IF $score > 0.8 → LOG("ok")\n'
    ast = parse(src)
    cond = ast.steps[0].body
    assert isinstance(cond, Conditional)
    assert "$score" in cond.condition


# ── Test blocks ─────────────────────────────────────────────────


def test_test_block_parsed():
    src = (
        '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. LOG("x")\n'
        '@test:smoke {\n  input: { msg: "hello" }\n  expected: { status = SUCCESS }\n}\n'
    )
    ast = parse(src)
    assert len(ast.tests) == 1
    assert ast.tests[0].name == "smoke"


def test_multiple_test_blocks():
    src = (
        '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. LOG("x")\n'
        "@test:happy {\n  input: {}\n}\n"
        "@test:sad {\n  input: {}\n}\n"
    )
    ast = parse(src)
    assert len(ast.tests) == 2


# ── Human mode ──────────────────────────────────────────────────


def test_human_mode_detected():
    src = (
        '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. LOG("x")\n'
        ";; HUMAN MODE\n;; This is a plain description.\n"
    )
    ast = parse(src)
    assert ast.human_mode is not None


# ── Schema file ─────────────────────────────────────────────────


def test_schema_named_blocks():
    src = "§schema:nodus v0.3\n§commands {\n  FETCH: fetch resource\n}\n"
    ast = parse(src)
    assert isinstance(ast, SchemaFile)
    assert "commands" in ast.sections
