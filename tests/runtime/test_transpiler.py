"""Tests for the NODUS Transpiler (NODUS \u2194 HUMAN mode).

Verifies the conversion logic between symbolic NODUS syntax and semantic
human-readable descriptions, including headers, triggers, inputs, rules,
steps, and reconstruction.
"""

from __future__ import annotations

from typing import Any

from runtime.interpreter.ast_nodes import (
    AbsoluteRule,
    CommandCall,
    Conditional,
    ContextDecl,
    ErrorDecl,
    FileHeader,
    FileType,
    ForLoop,
    InputDecl,
    InputField,
    NodusTestBlock,
    OutputDecl,
    ParallelBlock,
    Preference,
    RuntimeBlock,
    Step,
    Trigger,
    UntilLoop,
    WorkflowFile,
)
from runtime.interpreter.transpiler import Transpiler


def make_wf(**kwargs: Any) -> WorkflowFile:
    """Create a mock WorkflowFile for testing.

    Args:
        **kwargs: Fields to set on the WorkflowFile.

    Returns:
        A populated WorkflowFile instance.
    """
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="test_wf", version="v1.0")
    wf.runtime = RuntimeBlock(core="core/schema.nodus", mode="production")
    for k, v in kwargs.items():
        setattr(wf, k, v)
    return wf


# ───────────────────────────────────────────────────────────────────────────
# to_human: header
# ───────────────────────────────────────────────────────────────────────────


def test_human_includes_workflow_name() -> None:
    """Verify that humanized output includes the workflow name."""
    wf = make_wf()
    out = Transpiler().to_human(wf)
    assert "test_wf" in out


def test_human_includes_workflow_label() -> None:
    """Verify that humanized output includes the workflow label."""
    wf = make_wf()
    out = Transpiler().to_human(wf)
    assert "WORKFLOW:" in out


# ───────────────────────────────────────────────────────────────────────────
# to_human: triggers
# ───────────────────────────────────────────────────────────────────────────


def test_human_includes_trigger() -> None:
    """Verify that humanized output includes trigger descriptions."""
    t = Trigger(condition="new_mention", action="RUN(wf:test_wf)")
    wf = make_wf(triggers=[t])
    out = Transpiler().to_human(wf)
    assert "TRIGGER:" in out
    assert "mention" in out.lower()


def test_human_schedule_trigger() -> None:
    """Verify that humanized output includes schedule-based triggers."""
    t = Trigger(condition="schedule:08:00", action="RUN(wf:test_wf)")
    wf = make_wf(triggers=[t])
    out = Transpiler().to_human(wf)
    assert "08:00" in out


# ───────────────────────────────────────────────────────────────────────────
# to_human: input
# ───────────────────────────────────────────────────────────────────────────


def test_human_includes_input() -> None:
    """Verify that humanized output includes input field descriptions."""
    wf = make_wf(
        input_decl=InputDecl(
            fields=[
                InputField(name="msg", type_name="str"),
                InputField(name="url", type_name="url"),
            ]
        )
    )
    out = Transpiler().to_human(wf)
    assert "INPUT:" in out
    assert "msg" in out
    assert "url" in out


def test_human_optional_field_shows_default() -> None:
    """Verify that optionally provided default values are shown in human mode."""
    wf = make_wf(
        input_decl=InputDecl(
            fields=[
                InputField(
                    name="tone", type_name="str", optional=True, default="neutral"
                ),
            ]
        )
    )
    out = Transpiler().to_human(wf)
    assert "neutral" in out


# ───────────────────────────────────────────────────────────────────────────
# to_human: rules
# ───────────────────────────────────────────────────────────────────────────


def test_human_includes_rules() -> None:
    """Verify that humanized output includes validation rules."""
    wf = make_wf(
        rules=[AbsoluteRule(rule_type="NEVER", content="publish without validate")]
    )
    out = Transpiler().to_human(wf)
    assert "RULES:" in out
    assert "NEVER" in out


def test_human_includes_preferences() -> None:
    """Verify that humanized output includes preference rules."""
    wf = make_wf(preferences=[Preference(preferred="empathetic", over="neutral")])
    out = Transpiler().to_human(wf)
    assert "Prefer empathetic" in out


# ───────────────────────────────────────────────────────────────────────────
# to_human: steps
# ───────────────────────────────────────────────────────────────────────────


def test_human_includes_steps() -> None:
    """Verify that humanized output includes the steps section."""
    cmd = CommandCall(name="FETCH", args=["$in.url"], pipeline_target="$raw")
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_human(wf)
    assert "STEPS:" in out
    assert "Fetch" in out


def test_human_step_with_comment() -> None:
    """Verify that humanized output uses step comments as descriptions if present."""
    step = Step(number=1, comment=";; \u2014 Fetch the content")
    wf = make_wf(steps=[step])
    out = Transpiler().to_human(wf)
    assert "Fetch the content" in out


def test_human_conditional_step() -> None:
    """Verify that humanized output includes conditional logic."""
    cond = Conditional(condition="$raw = null", break_flag=True)
    wf = make_wf(steps=[Step(number=1, body=cond)])
    out = Transpiler().to_human(wf)
    assert "IF" in out
    assert "$raw" in out


def test_human_for_loop_step() -> None:
    """Verify that humanized output includes for-each loop logic."""
    loop = ForLoop(variable="$item", collection="$items", body=[])
    wf = make_wf(steps=[Step(number=1, body=loop)])
    out = Transpiler().to_human(wf)
    assert "For each" in out


def test_human_until_loop_step() -> None:
    """Verify that humanized output includes until-loop logic."""
    loop = UntilLoop(condition="$quality > 0.8", max_iterations=3, body=[])
    wf = make_wf(steps=[Step(number=1, body=loop)])
    out = Transpiler().to_human(wf)
    assert "Repeat until" in out
    assert "3" in out


def test_human_parallel_step() -> None:
    """Verify that humanized output includes parallel block logic."""
    block = ParallelBlock(branches=[], join_target="$result")
    wf = make_wf(steps=[Step(number=1, body=block)])
    out = Transpiler().to_human(wf)
    assert "parallel" in out.lower()


# ───────────────────────────────────────────────────────────────────────────
# to_human: output and error
# ───────────────────────────────────────────────────────────────────────────


def test_human_includes_output() -> None:
    """Verify that humanized output includes the output declaration."""
    wf = make_wf(output_decl=OutputDecl(variable="$out"))
    out = Transpiler().to_human(wf)
    assert "OUTPUT:" in out


def test_human_includes_error_handler() -> None:
    """Verify that humanized output includes error handlers."""
    wf = make_wf(error_decl=ErrorDecl(raw="ESCALATE(human)"))
    out = Transpiler().to_human(wf)
    assert "ON ERROR:" in out
    assert "human" in out.lower()


# ───────────────────────────────────────────────────────────────────────────
# to_human: command humanization
# ───────────────────────────────────────────────────────────────────────────


def test_humanize_command_gen() -> None:
    """Verify that command names are correctly mapped to verbs."""
    cmd = CommandCall(name="GEN", args=["reply"], pipeline_target="$draft")
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_human(wf)
    assert "Generate" in out


def test_humanize_command_validate_with_validators() -> None:
    """Verify that command validators are listed in human mode."""
    cmd = CommandCall(
        name="VALIDATE", args=["$draft"], validators=["^brand_voice", "^no_pii"]
    )
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_human(wf)
    assert "brand_voice" in out
    assert "no_pii" in out


def test_humanize_command_analyze_with_flags() -> None:
    """Verify that command flags are listed in human mode."""
    cmd = CommandCall(name="ANALYZE", args=["$raw"], flags=["sentiment", "intent"])
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_human(wf)
    assert "sentiment" in out
    assert "intent" in out


# ───────────────────────────────────────────────────────────────────────────
# to_nodus: reconstruction
# ───────────────────────────────────────────────────────────────────────────


def test_nodus_includes_header() -> None:
    """Verify that reconstructed output includes the §wf header."""
    wf = make_wf()
    out = Transpiler().to_nodus(wf)
    assert "\u00a7wf:test_wf v1.0" in out


def test_nodus_includes_runtime() -> None:
    """Verify that reconstructed output includes the §runtime block."""
    wf = make_wf()
    out = Transpiler().to_nodus(wf)
    assert "\u00a7runtime:" in out
    assert "core/schema.nodus" in out


def test_nodus_includes_rules() -> None:
    """Verify that reconstructed output includes validation rules."""
    wf = make_wf(
        rules=[AbsoluteRule(rule_type="NEVER", content="publish without validate")]
    )
    out = Transpiler().to_nodus(wf)
    assert "!!NEVER:" in out


def test_nodus_includes_preferences() -> None:
    """Verify that reconstructed output includes preference rules."""
    wf = make_wf(preferences=[Preference(preferred="empathetic", over="neutral")])
    out = Transpiler().to_nodus(wf)
    assert "!PREF:" in out
    assert "OVER" in out


def test_nodus_includes_steps() -> None:
    """Verify that reconstructed output includes the @steps section."""
    cmd = CommandCall(name="LOG", args=["$out"], pipeline_target=None)
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_nodus(wf)
    assert "@steps:" in out
    assert "LOG" in out


def test_nodus_pipeline_arrow() -> None:
    """Verify that reconstructed commands include pipeline arrows for targets."""
    cmd = CommandCall(name="FETCH", args=["$in.url"], pipeline_target="$raw")
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_nodus(wf)
    assert "\u2192" in out
    assert "$raw" in out


def test_nodus_includes_tests() -> None:
    """Verify that reconstructed output includes @test blocks."""
    test_block = NodusTestBlock(name="smoke", raw_lines=['input: { msg: "hello" }'])
    wf = make_wf(steps=[], tests=[test_block])
    out = Transpiler().to_nodus(wf)
    assert "@test:smoke" in out


def test_nodus_includes_input_decl() -> None:
    """Verify that reconstructed output includes @in declarations."""
    wf = make_wf(
        input_decl=InputDecl(
            fields=[
                InputField(name="msg", type_name="str"),
            ]
        )
    )
    out = Transpiler().to_nodus(wf)
    assert "@in:" in out
    assert "msg" in out


def test_nodus_optional_field_has_question_mark() -> None:
    """Verify that optional input fields are marked with a question mark (?) in Nodus mode."""
    wf = make_wf(
        input_decl=InputDecl(
            fields=[
                InputField(
                    name="tone", type_name="str", optional=True, default="neutral"
                ),
            ]
        )
    )
    out = Transpiler().to_nodus(wf)
    assert "tone?" in out


def test_nodus_includes_context() -> None:
    """Verify that reconstructed output includes @ctx declarations."""
    wf = make_wf(context_decl=ContextDecl(contexts=["brand_voice"]))
    out = Transpiler().to_nodus(wf)
    assert "@ctx:" in out
    assert "brand_voice" in out


# ───────────────────────────────────────────────────────────────────────────
# _humanize_var
# ───────────────────────────────────────────────────────────────────────────


def test_humanize_var_strips_dollar() -> None:
    """Verify that humanizing a variable strips the leading dollar sign."""
    t = Transpiler()
    assert t._humanize_var("$out") == "out"


def test_humanize_var_dotted() -> None:
    """Verify that humanizing a dotted variable uses an arrow separator."""
    t = Transpiler()
    assert t._humanize_var("$meta.intent") == "meta \u2192 intent"


def test_humanize_var_empty() -> None:
    """Verify that humanize_var handles empty strings."""
    t = Transpiler()
    assert t._humanize_var("") == ""


# ───────────────────────────────────────────────────────────────────────────
# _humanize_rule
# ───────────────────────────────────────────────────────────────────────────


def test_humanize_rule_lowercases() -> None:
    """Verify that humanized rules are lowercased for readability."""
    t = Transpiler()
    result = t._humanize_rule("PUBLISH WITHOUT VALIDATE")
    assert result == result.lower()


def test_humanize_rule_replaces_out() -> None:
    """Verify that humanized rules replace $out with 'the output'."""
    t = Transpiler()
    result = t._humanize_rule("check $out value")
    assert "the output" in result
