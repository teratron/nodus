"""Tests for the NODUS Executor.

Verifies the implementation of ExecutionContext, NodusResult, basic execution flow,
rule enforcement, conditional evaluation, looping mechanisms, and parallel execution.
"""

from __future__ import annotations

from typing import Any

from runtime.interpreter.ast_nodes import (
    AbsoluteRule,
    CommandCall,
    Conditional,
    FileHeader,
    FileType,
    ForLoop,
    InputDecl,
    InputField,
    OutputDecl,
    ParallelBlock,
    RuntimeBlock,
    Step,
    UntilLoop,
    WorkflowFile,
)
from runtime.interpreter.executor import (
    AnthropicProvider,
    ExecutionContext,
    Executor,
    NodusResult,
    StubProvider,
)


def make_wf(
    steps: list[Step] | None = None,
    rules: list[AbsoluteRule] | None = None,
    input_fields: list[InputField] | None = None,
    output_var: str = "$out",
) -> WorkflowFile:
    """Create a mock WorkflowFile for testing purposes.

    Args:
        steps: Optional list of Step nodes.
        rules: Optional list of AbsoluteRule nodes.
        input_fields: Optional list of InputField nodes.
        output_var: The name of the output variable.

    Returns:
        A populated WorkflowFile instance.
    """
    wf = WorkflowFile()
    wf.header = FileHeader(file_type=FileType.WORKFLOW, name="test", version="v1.0")
    wf.runtime = RuntimeBlock(core="schema.nodus")
    wf.steps = steps or []
    wf.rules = rules or []
    if input_fields:
        wf.input_decl = InputDecl(fields=input_fields)
    wf.output_decl = OutputDecl(variable=output_var)
    return wf


# ───────────────────────────────────────────────────────────────────────────
# NodusResult
# ───────────────────────────────────────────────────────────────────────────


def test_result_default_status() -> None:
    """Verify that a new NodusResult defaults to 'ok' status."""
    r = NodusResult()
    assert r.status == "ok"


def test_result_to_dict_keys() -> None:
    """Verify that to_dict() returns all expected result fields."""
    r = NodusResult()
    d = r.to_dict()
    assert "status" in d
    assert "out" in d
    assert "log" in d
    assert "errors" in d
    assert "flags" in d


# ───────────────────────────────────────────────────────────────────────────
# ModelProvider.model_id
# ───────────────────────────────────────────────────────────────────────────


def test_stub_provider_model_id() -> None:
    """Verify that StubProvider reports its model_id."""
    assert StubProvider().model_id == "nodus-stub"


def test_anthropic_provider_model_id() -> None:
    """Verify that AnthropicProvider reports its model_id."""
    assert AnthropicProvider().model_id == "anthropic-stub"


def test_result_agent_id_from_provider() -> None:
    """Verify that execute() propagates provider.model_id to result.agent_id."""
    wf = make_wf(steps=[])
    executor = Executor(provider=StubProvider())
    result = executor.execute(wf)
    assert result.agent_id == "nodus-stub"


def test_result_agent_id_custom_provider() -> None:
    """Verify agent_id with a different provider."""
    wf = make_wf(steps=[])
    executor = Executor(provider=AnthropicProvider())
    result = executor.execute(wf)
    assert result.agent_id == "anthropic-stub"


# ───────────────────────────────────────────────────────────────────────────
# ExecutionContext
# ───────────────────────────────────────────────────────────────────────────


def test_ctx_set_and_get_var() -> None:
    """Verify variable storage and retrieval in ExecutionContext."""
    ctx = ExecutionContext()
    ctx.set_var("$foo", 42)
    assert ctx.get_var("$foo") == 42


def test_ctx_get_var_dotted() -> None:
    """Verify retrieval of nested properties via dotted variable names."""
    ctx = ExecutionContext()
    ctx.set_var("meta", {"intent": "praise"})
    assert ctx.get_var("$meta.intent") == "praise"


def test_ctx_out_lock() -> None:
    """Verify that $out variable is immutable when out_locked is True."""
    ctx = ExecutionContext()
    ctx.set_var("$out", "first")
    ctx.out_locked = True
    ctx.set_var("$out", "second")
    assert ctx.get_var("$out") == "first"
    assert len(ctx.errors) == 1


def test_ctx_out_lock_adds_error() -> None:
    """Verify that attempting to overwrite a locked $out adds a RULE_VIOLATION error."""
    ctx = ExecutionContext()
    ctx.out_locked = True
    ctx.set_var("$out", "value")
    assert any(
        "out" in str(e).lower() or "RULE_VIOLATION" in str(e) for e in ctx.errors
    )


def test_ctx_log_step() -> None:
    """Verify that log_step adds an entry to the execution log."""
    ctx = ExecutionContext()
    ctx.log_step(1, "FETCH", {"data": "x"})
    assert len(ctx.log) == 1
    assert ctx.log[0]["command"] == "FETCH"
    assert ctx.log[0]["step"] == 1


# ───────────────────────────────────────────────────────────────────────────
# Basic execution
# ───────────────────────────────────────────────────────────────────────────


def test_execute_empty_workflow() -> None:
    """Verify that a workflow with no steps executes successfully."""
    wf = make_wf()
    result = Executor().execute(wf)
    assert result.status == "ok"


def test_execute_non_workflow_fails() -> None:
    """Verify that executor fails gracefully when passed invalid input."""
    result = Executor().execute("not a workflow")  # type: ignore[arg-type]
    assert result.status == "failed"
    assert len(result.errors) > 0


def test_execute_log_command() -> None:
    """Verify execution of a simple LOG command."""
    cmd = CommandCall(name="LOG", args=["$out"])
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    result = Executor().execute(wf)
    assert result.status == "ok"
    assert len(result.log) == 1


def test_execute_assigns_pipeline_target() -> None:
    """Verify that command results are correctly assigned to pipeline targets (→)."""
    cmd = CommandCall(
        name="ANALYZE", args=["$raw"], flags=["sentiment"], pipeline_target="$meta"
    )
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    result = Executor().execute(wf, input_data={"raw": "hello"})
    assert result.status == "ok"


def test_execute_input_data_loaded() -> None:
    """Verify that provided input_data is accessible via $in variable."""
    wf = make_wf(input_fields=[InputField(name="msg", type_name="str")])
    executor = Executor()
    # capture ctx by using a custom handler
    captured: dict[str, Any] = {}

    def handler(ctx: ExecutionContext, cmd: CommandCall) -> str:
        captured["in"] = ctx.get_var("$in")
        return "ok"

    executor.register_handler("LOG", handler)
    cmd = CommandCall(name="LOG", args=["$in"])
    wf.steps = [Step(number=1, body=cmd)]
    executor.execute(wf, input_data={"msg": "hello"})
    assert captured.get("in", {}).get("msg") == "hello"


# ───────────────────────────────────────────────────────────────────────────
# Break signal
# ───────────────────────────────────────────────────────────────────────────


def test_break_stops_execution() -> None:
    """Verify that !BREAK signal terminates workflow execution immediately."""
    cond = Conditional(condition="true", break_flag=True)
    after = CommandCall(name="LOG", args=["after"])
    wf = make_wf(
        steps=[
            Step(number=1, body=cond),
            Step(number=2, body=after),
        ]
    )
    result = Executor().execute(wf)
    assert result.status == "aborted"
    # step 2 should not have run
    assert not any(e.get("command") == "LOG" for e in result.log)


# ───────────────────────────────────────────────────────────────────────────
# Rule enforcement
# ───────────────────────────────────────────────────────────────────────────


def test_never_publish_without_validate_raises() -> None:
    """Verify that !!NEVER rule prevents command execution without prior validation."""
    rule = AbsoluteRule(rule_type="NEVER", content="publish WITHOUT validate")
    publish = CommandCall(name="PUBLISH", args=["$draft"])
    wf = make_wf(steps=[Step(number=1, body=publish)], rules=[rule])
    result = Executor().execute(wf)
    assert result.status == "failed"
    assert any("RULE_VIOLATION" in str(e) for e in result.errors)


def test_never_rule_ok_when_validated_first() -> None:
    """Verify that !!NEVER rule allows execution if validation has occurred."""
    rule = AbsoluteRule(rule_type="NEVER", content="publish WITHOUT validate")
    validate_cmd = CommandCall(name="VALIDATE", args=["$draft"], pipeline_target="$v")
    publish = CommandCall(name="PUBLISH", args=["$v"])
    wf = make_wf(
        steps=[
            Step(number=1, body=validate_cmd),
            Step(number=2, body=publish),
        ],
        rules=[rule],
    )
    result = Executor().execute(wf)
    assert result.status == "ok"


# ───────────────────────────────────────────────────────────────────────────
# Custom handler
# ───────────────────────────────────────────────────────────────────────────


def test_register_custom_handler() -> None:
    """Verify that custom handlers can be registered and invoked."""
    executor = Executor()
    called: dict[str, bool] = {}

    def my_handler(ctx: ExecutionContext, cmd: CommandCall) -> str:
        called["yes"] = True
        return "custom_result"

    executor.register_handler("FETCH", my_handler)
    cmd = CommandCall(name="FETCH", args=["http://example.com"], pipeline_target="$raw")
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    executor.execute(wf)
    assert called.get("yes") is True


def test_unknown_command_adds_flag() -> None:
    """Verify that executing a command with no handler adds a flag to the result."""
    cmd = CommandCall(name="MY_CUSTOM_CMD", args=[])
    wf = make_wf(steps=[Step(number=1, body=cmd)])
    result = Executor().execute(wf)
    assert any("MY_CUSTOM_CMD" in f for f in result.flags)


# ───────────────────────────────────────────────────────────────────────────
# Condition evaluation
# ───────────────────────────────────────────────────────────────────────────


def test_condition_equals_true() -> None:
    """Verify simple equality evaluation in conditions."""
    ctx = ExecutionContext()
    ctx.set_var("score", 0.9)
    assert Executor()._evaluate_condition(ctx, "$score = 0.9") is True


def test_condition_gt() -> None:
    """Verify greater-than (>) evaluation in conditions."""
    ctx = ExecutionContext()
    ctx.set_var("score", 0.9)
    assert Executor()._evaluate_condition(ctx, "$score > 0.8") is True


def test_condition_lt_false() -> None:
    """Verify less-than (<) evaluation in conditions."""
    ctx = ExecutionContext()
    ctx.set_var("score", 0.9)
    assert Executor()._evaluate_condition(ctx, "$score < 0.5") is False


def test_condition_contains() -> None:
    """Verify CONTAINS operator for list values."""
    ctx = ExecutionContext()
    ctx.set_var("flags", ["ESCALATE:human", "ROUTE:support"])
    assert Executor()._evaluate_condition(ctx, "$flags CONTAINS ESCALATE:human") is True


def test_condition_and() -> None:
    """Verify logical AND evaluation."""
    ctx = ExecutionContext()
    ctx.set_var("a", 1)
    ctx.set_var("b", 2)
    assert Executor()._evaluate_condition(ctx, "$a = 1 AND $b = 2") is True


def test_condition_or() -> None:
    """Verify logical OR evaluation."""
    ctx = ExecutionContext()
    ctx.set_var("a", 1)
    assert Executor()._evaluate_condition(ctx, "$a = 99 OR $a = 1") is True


def test_condition_empty_is_true() -> None:
    """Verify that an empty condition string evaluates to True."""
    ctx = ExecutionContext()
    assert Executor()._evaluate_condition(ctx, "") is True


# ───────────────────────────────────────────────────────────────────────────
# ~FOR loop
# ───────────────────────────────────────────────────────────────────────────


def test_for_loop_iterates() -> None:
    """Verify that ~FOR loop correctly iterates over collection values."""
    collected: list[Any] = []
    executor = Executor()

    def log_handler(ctx: ExecutionContext, cmd: CommandCall) -> str:
        collected.append(ctx.get_var("$item"))
        return "ok"

    executor.register_handler("LOG", log_handler)

    body_cmd = CommandCall(name="LOG", args=["$item"])
    loop = ForLoop(variable="$item", collection="$items", body=[body_cmd])
    wf = make_wf(steps=[Step(number=1, body=loop)])
    executor.execute(wf, input_data={"items": ["a", "b", "c"]})
    assert collected == ["a", "b", "c"]


# ───────────────────────────────────────────────────────────────────────────
# ~UNTIL loop
# ───────────────────────────────────────────────────────────────────────────


def test_until_loop_max_reached_adds_flag() -> None:
    """Verify that hitting MAX iterations in ~UNTIL loop adds a flag."""
    # condition never becomes true → should hit MAX
    body_cmd = CommandCall(name="LOG", args=["iter"])
    loop = UntilLoop(condition="$x = done", max_iterations=2, body=[body_cmd])
    wf = make_wf(steps=[Step(number=1, body=loop)])
    result = Executor().execute(wf)
    assert "NODUS:MAX_REACHED" in result.flags


def test_until_loop_exits_when_condition_met() -> None:
    """Verify that ~UNTIL loop terminates when its condition becomes true."""
    executor = Executor()
    counter = {"n": 0}

    def increment(ctx: ExecutionContext, cmd: CommandCall) -> str:
        counter["n"] += 1
        ctx.set_var("$x", "done" if counter["n"] >= 2 else "waiting")
        return "ok"

    executor.register_handler("LOG", increment)

    body_cmd = CommandCall(name="LOG", args=["iter"])
    loop = UntilLoop(condition="$x = done", max_iterations=5, body=[body_cmd])
    wf = make_wf(steps=[Step(number=1, body=loop)])
    result = executor.execute(wf)
    assert "NODUS:MAX_REACHED" not in result.flags
    assert counter["n"] == 2


# ───────────────────────────────────────────────────────────────────────────
# ~PARALLEL block
# ───────────────────────────────────────────────────────────────────────────


def test_parallel_block_runs_all_branches() -> None:
    """Verify that ~PARALLEL block executes all included branches."""
    called: list[str] = []
    executor = Executor()

    def handler(ctx: ExecutionContext, cmd: CommandCall) -> str:
        called.append(cmd.args[0] if cmd.args else "?")
        return "ok"

    executor.register_handler("LOG", handler)

    b1 = CommandCall(name="LOG", args=["branch1"])
    b2 = CommandCall(name="LOG", args=["branch2"])
    block = ParallelBlock(branches=[b1, b2], join_target="$result")
    wf = make_wf(steps=[Step(number=1, body=block)])
    executor.execute(wf)
    assert "branch1" in called
    assert "branch2" in called


# ───────────────────────────────────────────────────────────────────────────
# Session variables
# ───────────────────────────────────────────────────────────────────────────


def test_session_var_initialized() -> None:
    """Verify that $session metadata is initialized in the execution context."""
    wf = make_wf()
    ctx_captured: dict[str, Any] = {}
    executor = Executor()

    def handler(ctx: ExecutionContext, cmd: CommandCall) -> str:
        ctx_captured["session"] = ctx.get_var("$session")
        return "ok"

    executor.register_handler("LOG", handler)
    cmd = CommandCall(name="LOG", args=["$session"])
    wf.steps = [Step(number=1, body=cmd)]
    executor.execute(wf)
    s = ctx_captured.get("session", {})
    assert "id" in s
    assert "ts_start" in s
