"""Tests for the NODUS Validator (lint rules).

Verifies validation logic for required runtime blocks, input field defaults,
loop constraints, file naming, and missing handlers/tests.
"""

from __future__ import annotations

from runtime.interpreter.ast_nodes import (
    CommandCall,
    Diagnostic,
    ErrorDecl,
    FileHeader,
    FileType,
    InputDecl,
    InputField,
    Node,
    OutputDecl,
    RuntimeBlock,
    Severity,
    Step,
    UntilLoop,
    WorkflowFile,
)
from runtime.interpreter.parser import Parser
from runtime.interpreter.validator import Validator


def parse(source: str, filename: str = "test.nodus") -> Node | None:
    """Parse source string into an AST.

    Args:
        source: Input code string.
        filename: Optional filename.

    Returns:
        The root AST node.
    """
    return Parser().parse(source, filename=filename)


def validate(source: str, filename: str = "test.nodus") -> list[Diagnostic]:
    """Parse and validate source string.

    Args:
        source: Input code string.
        filename: Optional filename.

    Returns:
        List of Diagnostic objects.
    """
    ast = parse(source, filename=filename)
    assert ast is not None
    return Validator().validate(ast, filename=filename)


def codes(diags: list[Diagnostic]) -> list[str]:
    """Extract diagnostic codes from a list of diagnostics.

    Args:
        diags: List of Diagnostics.

    Returns:
        List of alphanumeric codes (e.g. E001).
    """
    return [d.code for d in diags]


def severities(diags: list[Diagnostic]) -> list[Severity]:
    """Extract severity levels from a list of diagnostics.

    Args:
        diags: List of Diagnostics.

    Returns:
        List of Severity enum values.
    """
    return [d.severity for d in diags]


# ───────────────────────────────────────────────────────────────────────────
# E001: runtime present
# ───────────────────────────────────────────────────────────────────────────


def test_e001_missing_runtime() -> None:
    """Verify E001 error when §runtime block is missing in workflow."""
    src = '§wf:foo v1.0\n@steps:\n  1. LOG("x")\n'
    diags = validate(src)
    assert "E001" in codes(diags)


def test_e001_no_error_when_runtime_present() -> None:
    """Verify no E001 error when §runtime block is present."""
    src = '§wf:foo v1.0\n§runtime: {}\n@steps:\n  1. LOG("x")\n'
    diags = validate(src)
    assert "E001" not in codes(diags)


# ───────────────────────────────────────────────────────────────────────────
# E009: required field with default
# ───────────────────────────────────────────────────────────────────────────


def test_e009_required_field_has_default() -> None:
    """Verify E009 error when a required input field has a default value."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    wf.input_decl = InputDecl(
        fields=[
            InputField(name="msg", type_name="str", optional=False, default="hello")
        ]
    )
    diags = Validator().validate(wf)
    assert "E009" in codes(diags)


def test_e009_optional_field_with_default_ok() -> None:
    """Verify no E009 error when an optional input field has a default value."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    wf.input_decl = InputDecl(
        fields=[
            InputField(name="tone", type_name="str", optional=True, default="neutral")
        ]
    )
    diags = Validator().validate(wf)
    assert "E009" not in codes(diags)


# ───────────────────────────────────────────────────────────────────────────
# E010: ~UNTIL must have MAX
# ───────────────────────────────────────────────────────────────────────────


def test_e010_until_without_max() -> None:
    """Verify E010 error when ~UNTIL loop is missing MAX constraint."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    loop = UntilLoop(condition="$quality > 0.8", max_iterations=None)
    step = Step(number=1, body=loop)
    wf.steps = [step]
    diags = Validator().validate(wf)
    assert "E010" in codes(diags)


def test_e010_until_with_max_ok() -> None:
    """Verify no E010 error when ~UNTIL loop has MAX constraint."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    loop = UntilLoop(condition="$quality > 0.8", max_iterations=3)
    step = Step(number=1, body=loop)
    wf.steps = [step]
    diags = Validator().validate(wf)
    assert "E010" not in codes(diags)


# ───────────────────────────────────────────────────────────────────────────
# E012: name matches filename
# ───────────────────────────────────────────────────────────────────────────


def test_e012_name_mismatch() -> None:
    """Verify E012 error when workflow name doesn't match filename."""
    src = "§wf:wrong_name v1.0\n§runtime: {}\n@steps:\n"
    diags = validate(src, filename="correct_name.nodus")
    assert "E012" in codes(diags)


def test_e012_name_matches() -> None:
    """Verify no E012 error when workflow name matches filename."""
    src = "§wf:my_flow v1.0\n§runtime: {}\n@steps:\n"
    diags = validate(src, filename="my_flow.nodus")
    assert "E012" not in codes(diags)


# ───────────────────────────────────────────────────────────────────────────
# W001: @err handler
# ───────────────────────────────────────────────────────────────────────────


def test_w001_no_err_handler() -> None:
    """Verify W001 warning when @err handler is missing."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    diags = Validator().validate(wf)
    assert "W001" in codes(diags)


def test_w001_with_err_handler() -> None:
    """Verify no W001 warning when @err handler is provided."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    wf.error_decl = ErrorDecl(raw="ESCALATE(human)")
    diags = Validator().validate(wf)
    assert "W001" not in codes(diags)


# ───────────────────────────────────────────────────────────────────────────
# W002: has tests
# ───────────────────────────────────────────────────────────────────────────


def test_w002_no_tests() -> None:
    """Verify W002 warning when no @test blocks are present."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    diags = Validator().validate(wf)
    assert "W002" in codes(diags)


# ───────────────────────────────────────────────────────────────────────────
# W003: human mode
# ───────────────────────────────────────────────────────────────────────────


def test_w003_no_human_mode() -> None:
    """Verify W003 warning when HUMAN MODE documentation is missing."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    diags = Validator().validate(wf)
    assert "W003" in codes(diags)


def test_w003_with_human_mode() -> None:
    """Verify no W003 warning when HUMAN MODE documentation is present."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    wf.human_mode = "WORKFLOW: foo\nThis does something."
    diags = Validator().validate(wf)
    assert "W003" not in codes(diags)


# ───────────────────────────────────────────────────────────────────────────
# W004: step count
# ───────────────────────────────────────────────────────────────────────────


def test_w004_too_many_steps() -> None:
    """Verify W004 warning when workflow exceeds 20 steps."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    wf.steps = [Step(number=i) for i in range(1, 22)]  # 21 steps
    diags = Validator().validate(wf)
    assert "W004" in codes(diags)


def test_w004_ok_within_limit() -> None:
    """Verify no W004 warning when workflow has exactly 20 steps."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    wf.steps = [Step(number=i) for i in range(1, 21)]  # 20 steps
    diags = Validator().validate(wf)
    assert "W004" not in codes(diags)


# ───────────────────────────────────────────────────────────────────────────
# W007: $out assigned
# ───────────────────────────────────────────────────────────────────────────


def test_w007_out_not_assigned() -> None:
    """Verify W007 warning when the declared @out variable is never assigned."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    wf.output_decl = OutputDecl(variable="$out")
    cmd = CommandCall(name="LOG", args=["$draft"], pipeline_target="$draft")
    wf.steps = [Step(number=1, body=cmd)]
    diags = Validator().validate(wf)
    assert "W007" in codes(diags)


def test_w007_out_assigned() -> None:
    """Verify no W007 warning when the declared @out variable is assigned."""
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="foo", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    wf.output_decl = OutputDecl(variable="$out")
    cmd = CommandCall(name="GEN", args=["reply"], pipeline_target="$out")
    wf.steps = [Step(number=1, body=cmd)]
    diags = Validator().validate(wf)
    assert "W007" not in codes(diags)


# ───────────────────────────────────────────────────────────────────────────
# Severity values
# ───────────────────────────────────────────────────────────────────────────


def test_severity_values_are_strings() -> None:
    """Verify Severity enum values are lowercase strings."""
    assert Severity.ERROR.value == "error"
    assert Severity.WARNING.value == "warning"
    assert Severity.INFO.value == "info"


def test_diagnostic_severity_in_validate() -> None:
    """Verify that validation errors have the ERROR severity level."""
    wf = WorkflowFile()
    # no runtime → E001 error
    diags = Validator().validate(wf)
    errors = [d for d in diags if d.severity == Severity.ERROR]
    assert len(errors) > 0
