"""Tests for the NODUS Transpiler (NODUS ↔ HUMAN mode)."""

from runtime.interpreter.transpiler import Transpiler
from runtime.interpreter.ast_nodes import (
    WorkflowFile,
    FileHeader,
    FileType,
    RuntimeBlock,
    AbsoluteRule,
    Preference,
    InputDecl,
    InputField,
    OutputDecl,
    ContextDecl,
    ErrorDecl,
    Step,
    CommandCall,
    Conditional,
    ForLoop,
    UntilLoop,
    ParallelBlock,
    Trigger,
    TestBlock,
)


def make_wf(**kwargs):
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="test_wf", version="v1.0")
    wf.runtime = RuntimeBlock(core="core/schema.nodus", mode="production")
    for k, v in kwargs.items():
        setattr(wf, k, v)
    return wf


# ── to_human: header ────────────────────────────────────────────


def test_human_includes_workflow_name():
    wf = make_wf()
    out = Transpiler().to_human(wf)
    assert "test_wf" in out


def test_human_includes_workflow_label():
    wf = make_wf()
    out = Transpiler().to_human(wf)
    assert "WORKFLOW:" in out


# ── to_human: triggers ──────────────────────────────────────────


def test_human_includes_trigger():
    t = Trigger(condition="new_mention", action="RUN(wf:test_wf)")
    wf = make_wf(triggers=[t])
    out = Transpiler().to_human(wf)
    assert "TRIGGER:" in out
    assert "mention" in out.lower()


def test_human_schedule_trigger():
    t = Trigger(condition="schedule:08:00", action="RUN(wf:test_wf)")
    wf = make_wf(triggers=[t])
    out = Transpiler().to_human(wf)
    assert "08:00" in out


# ── to_human: input ─────────────────────────────────────────────


def test_human_includes_input():
    wf = make_wf(input_decl=InputDecl(fields=[
        InputField(name="msg", type_name="str"),
        InputField(name="url", type_name="url"),
    ]))
    out = Transpiler().to_human(wf)
    assert "INPUT:" in out
    assert "msg" in out
    assert "url" in out


def test_human_optional_field_shows_default():
    wf = make_wf(input_decl=InputDecl(fields=[
        InputField(name="tone", type_name="str", optional=True, default="neutral"),
    ]))
    out = Transpiler().to_human(wf)
    assert "neutral" in out


# ── to_human: rules ─────────────────────────────────────────────


def test_human_includes_rules():
    wf = make_wf(rules=[AbsoluteRule(rule_type="NEVER", content="publish without validate")])
    out = Transpiler().to_human(wf)
    assert "RULES:" in out
    assert "NEVER" in out


def test_human_includes_preferences():
    wf = make_wf(preferences=[Preference(preferred="empathetic", over="neutral")])
    out = Transpiler().to_human(wf)
    assert "Prefer empathetic" in out


# ── to_human: steps ─────────────────────────────────────────────


def test_human_includes_steps():
    cmd = CommandCall(name="FETCH", args=["$in.url"], pipeline_target="$raw")
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_human(wf)
    assert "STEPS:" in out
    assert "Fetch" in out


def test_human_step_with_comment():
    step = Step(number=1, comment=";; — Fetch the content")
    wf = make_wf(steps=[step])
    out = Transpiler().to_human(wf)
    assert "Fetch the content" in out


def test_human_conditional_step():
    cond = Conditional(condition="$raw = null", break_flag=True)
    wf = make_wf(steps=[Step(number=1, body=cond)])
    out = Transpiler().to_human(wf)
    assert "IF" in out
    assert "$raw" in out


def test_human_for_loop_step():
    loop = ForLoop(variable="$item", collection="$items", body=[])
    wf = make_wf(steps=[Step(number=1, body=loop)])
    out = Transpiler().to_human(wf)
    assert "For each" in out


def test_human_until_loop_step():
    loop = UntilLoop(condition="$quality > 0.8", max_iterations=3, body=[])
    wf = make_wf(steps=[Step(number=1, body=loop)])
    out = Transpiler().to_human(wf)
    assert "Repeat until" in out
    assert "3" in out


def test_human_parallel_step():
    block = ParallelBlock(branches=[], join_target="$result")
    wf = make_wf(steps=[Step(number=1, body=block)])
    out = Transpiler().to_human(wf)
    assert "parallel" in out.lower()


# ── to_human: output and error ──────────────────────────────────


def test_human_includes_output():
    wf = make_wf(output_decl=OutputDecl(variable="$out"))
    out = Transpiler().to_human(wf)
    assert "OUTPUT:" in out


def test_human_includes_error_handler():
    wf = make_wf(error_decl=ErrorDecl(raw="ESCALATE(human)"))
    out = Transpiler().to_human(wf)
    assert "ON ERROR:" in out
    assert "human" in out.lower()


# ── to_human: command humanization ─────────────────────────────


def test_humanize_command_gen():
    cmd = CommandCall(name="GEN", args=["reply"], pipeline_target="$draft")
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_human(wf)
    assert "Generate" in out


def test_humanize_command_validate_with_validators():
    cmd = CommandCall(name="VALIDATE", args=["$draft"], validators=["^brand_voice", "^no_pii"])
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_human(wf)
    assert "brand_voice" in out
    assert "no_pii" in out


def test_humanize_command_analyze_with_flags():
    cmd = CommandCall(name="ANALYZE", args=["$raw"], flags=["sentiment", "intent"])
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_human(wf)
    assert "sentiment" in out
    assert "intent" in out


# ── to_nodus: reconstruction ────────────────────────────────────


def test_nodus_includes_header():
    wf = make_wf()
    out = Transpiler().to_nodus(wf)
    assert "§wf:test_wf v1.0" in out


def test_nodus_includes_runtime():
    wf = make_wf()
    out = Transpiler().to_nodus(wf)
    assert "§runtime:" in out
    assert "core/schema.nodus" in out


def test_nodus_includes_rules():
    wf = make_wf(rules=[AbsoluteRule(rule_type="NEVER", content="publish without validate")])
    out = Transpiler().to_nodus(wf)
    assert "!!NEVER:" in out


def test_nodus_includes_preferences():
    wf = make_wf(preferences=[Preference(preferred="empathetic", over="neutral")])
    out = Transpiler().to_nodus(wf)
    assert "!PREF:" in out
    assert "OVER" in out


def test_nodus_includes_steps():
    cmd = CommandCall(name="LOG", args=["$out"], pipeline_target=None)
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_nodus(wf)
    assert "@steps:" in out
    assert "LOG" in out


def test_nodus_pipeline_arrow():
    cmd = CommandCall(name="FETCH", args=["$in.url"], pipeline_target="$raw")
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    out = Transpiler().to_nodus(wf)
    assert "→" in out
    assert "$raw" in out


def test_nodus_includes_tests():
    test_block = TestBlock(name="smoke", raw_lines=["input: { msg: \"hello\" }"])
    wf = make_wf(steps=[], tests=[test_block])
    out = Transpiler().to_nodus(wf)
    assert "@test:smoke" in out


def test_nodus_includes_input_decl():
    wf = make_wf(input_decl=InputDecl(fields=[
        InputField(name="msg", type_name="str"),
    ]))
    out = Transpiler().to_nodus(wf)
    assert "@in:" in out
    assert "msg" in out


def test_nodus_optional_field_has_question_mark():
    wf = make_wf(input_decl=InputDecl(fields=[
        InputField(name="tone", type_name="str", optional=True, default="neutral"),
    ]))
    out = Transpiler().to_nodus(wf)
    assert "tone?" in out


def test_nodus_includes_context():
    wf = make_wf(context_decl=ContextDecl(contexts=["brand_voice"]))
    out = Transpiler().to_nodus(wf)
    assert "@ctx:" in out
    assert "brand_voice" in out


# ── _humanize_var ───────────────────────────────────────────────


def test_humanize_var_strips_dollar():
    t = Transpiler()
    assert t._humanize_var("$out") == "out"


def test_humanize_var_dotted():
    t = Transpiler()
    assert t._humanize_var("$meta.intent") == "meta → intent"


def test_humanize_var_empty():
    t = Transpiler()
    assert t._humanize_var("") == ""


# ── _humanize_rule no-op removed ────────────────────────────────


def test_humanize_rule_lowercases():
    t = Transpiler()
    result = t._humanize_rule("PUBLISH WITHOUT VALIDATE")
    assert result == result.lower()


def test_humanize_rule_replaces_out():
    t = Transpiler()
    result = t._humanize_rule("check $out value")
    assert "the output" in result
