"""NODUS Executor — runtime engine for .nodus workflows.

Walks the AST produced by the Parser and executes each step
according to the NODUS protocol. Command handlers are pluggable;
defaults are stubs that simulate execution without side effects.

The executor follows the boot sequence defined in AGENTS.md:
  1. LOAD schema     (resolve runtime block)
  2. READ !! rules   (internalize constraints)
  3. READ !PREF      (load soft preferences)
  4. READ @in/@ctx   (register inputs/context)
  5. READ @ON        (register triggers)
  6. EXECUTE @steps  (run the workflow)
"""

from __future__ import annotations

import abc
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .. import constants, settings
from .ast_nodes import (
    AbsoluteRule,
    CommandCall,
    Conditional,
    ForLoop,
    Node,
    ParallelBlock,
    Preference,
    Step,
    UntilLoop,
    WorkflowFile,
)

# ───────────────────────────────────────────────────────────────────────────
# Type Aliases
# ───────────────────────────────────────────────────────────────────────────

CommandHandler = Callable[["ExecutionContext", CommandCall], Any]


# ═══════════════════════════════════════════════════════════════════════════
# MODEL PROVIDERS
# ═══════════════════════════════════════════════════════════════════════════


class ModelProvider(abc.ABC):
    """Abstract base class for LLM providers."""

    @abc.abstractmethod
    def generate(self, prompt: str, modifiers: dict[str, Any]) -> str:
        """Generate text.

        Args:
            prompt: The instruction for generation.
            modifiers: Command modifiers (e.g., +tone).

        Returns:
            The generated text string.
        """
        ...

    @abc.abstractmethod
    def analyze(self, text: str, flags: list[str]) -> dict[str, Any]:
        """Analyze text.

        Args:
            text: The text to analyze.
            flags: Analysis flags (e.g., intent, sentiment).

        Returns:
            A dictionary containing analysis results.
        """
        ...


class StubProvider(ModelProvider):
    """Default provider that returns predefined stubs for testing."""

    def generate(self, prompt: str, modifiers: dict[str, Any]) -> str:
        """Generate a stub response based on settings templates."""
        tone = modifiers.get("+tone", "brand")
        return settings.STUB_GENERATE_TEMPLATE.format(prompt=prompt, tone=tone)

    def analyze(self, text: str, flags: list[str]) -> dict[str, Any]:
        """Return stub analysis results."""
        result: dict[str, Any] = {}
        for flag in flags:
            result[flag] = (
                settings.STUB_ANALYZE_VALUE
                if flag == "intent"
                else settings.STUB_ANALYZE_SCORE
            )
        return result


class AnthropicProvider(ModelProvider):
    """Example provider for Anthropic Claude (Stubbed)."""

    def generate(self, prompt: str, modifiers: dict[str, Any]) -> str:
        """Simulate real call to Anthropic API."""
        return f"[Generated via ANTHROPIC: {prompt}]"

    def analyze(self, text: str, flags: list[str]) -> dict[str, Any]:
        """Return simulated analysis results via Anthropic."""
        return {"intent": "analyzed_by_anthropic", "sentiment": 0.9}


# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION CONTEXT
# ═══════════════════════════════════════════════════════════════════════════


class ExecutionContext:
    """Runtime state for a single workflow execution.

    Internalizes variables, rules, preferences, and tracks logical locks.
    """

    def __init__(self) -> None:
        """Initialize the execution context."""
        self.variables: dict[str, Any] = {}
        self.rules: list[AbsoluteRule] = []
        self.preferences: list[Preference] = []
        self.log: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.flags: list[str] = []
        self.active_tone: str = "brand"
        self.out_locked: bool = False

    def set_var(self, name: str, value: Any) -> None:
        """Set a context variable.

        Args:
            name: Variable name (with or without $).
            value: The value to assign.

        Note:
            Respects $out lock if LOG() has already been called.
        """
        clean = name.lstrip("$")
        if clean == "out" and self.out_locked:
            self.errors.append(
                {
                    "code": constants.ERR_RULE_VIOLATION,
                    "reason": "Cannot modify $out after LOG() has been called.",
                }
            )
            return
        self.variables[clean] = value

    def get_var(self, name: str) -> Any:
        """Retrieve a variable value, supporting dot-notation.

        Args:
            name: Variable path (e.g., $in.user.name).

        Returns:
            The resolved value or None if not found.
        """
        clean = name.lstrip("$")
        parts = clean.split(".")
        val = self.variables.get(parts[0])
        for part in parts[1:]:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                return None
        return val

    def log_step(self, step_num: int, command: str, result: Any) -> None:
        """Record a single command execution in the workflow log.

        Args:
            step_num: Number of the executing step.
            command: Command name.
            result: The output of the command.
        """
        self.log.append(
            {
                "step": step_num,
                "command": command,
                "result": result,
                "ts": datetime.now(UTC).isoformat(),
            }
        )

    def check_rules(self, command: str, args: list[str]) -> str | None:
        """Audit a command against current absolute rules.

        Args:
            command: The command name to check.
            args: Command arguments.

        Returns:
            A violation description or None if safe.
        """
        cmd_upper = command.upper()
        args_lower = [str(a).lower() for a in args]

        for rule in self.rules:
            content = rule.content.strip()
            content_upper = content.upper()

            if rule.rule_type == "NEVER":
                # 1. Simple command name match (e.g., !!NEVER: DELETE)
                if content_upper == cmd_upper:
                    return f"!!NEVER: {content}"

                # 2. Command with specific arguments (e.g., !!NEVER: FETCH("http://evil.com"))
                if cmd_upper in content_upper:
                    # Check if any of the arguments mentioned in the rule are present in current call
                    if any(arg in content.lower() for arg in args_lower):
                        return f"!!NEVER: {content}"

                # 3. Conditional constraints (e.g., !!NEVER: publish WITHOUT validate)
                if (
                    cmd_upper == "PUBLISH"
                    and "WITHOUT" in content_upper
                    and "VALIDATE" in content_upper
                ):
                    validated = any(e.get("command") == "VALIDATE" for e in self.log)
                    if not validated:
                        return f"!!NEVER: {content}"

            elif rule.rule_type == "ALWAYS":
                # ALWAYS rules are mostly checked post-execution or in specific contexts.
                # Here we can check for MUST PRE-VALIDATE if that's the rule.
                pass

        return None


# ═══════════════════════════════════════════════════════════════════════════
# RESULTS
# ═══════════════════════════════════════════════════════════════════════════


class NodusResult:
    """NODUS:RESULT — the standard output architecture of every workflow.

    Encapsulates final state, logs, and metadata for external systems.
    """

    def __init__(self) -> None:
        """Initialize the result object with default state."""
        self.workflow: str = ""
        self.version: str = ""
        self.status: str = "ok"  # ok | partial | failed | aborted
        self.out: Any = None
        self.log: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.flags: list[str] = []
        self.ts_end: str = ""
        self.agent_id: str = settings.AGENT_ID

    def to_dict(self) -> dict[str, Any]:
        """Serialize the NODUS:RESULT to a dictionary.

        Returns:
            Dictionary containing all execution metadata.
        """
        return {
            "workflow": self.workflow,
            "version": self.version,
            "status": self.status,
            "out": self.out,
            "log": self.log,
            "errors": self.errors,
            "flags": self.flags,
            "ts_end": self.ts_end,
            "agent_id": self.agent_id,
        }


# ═══════════════════════════════════════════════════════════════════════════
# EXECUTOR ENGINE
# ═══════════════════════════════════════════════════════════════════════════


class Executor:
    """Core runtime engine for the NODUS language.

    Orchestrates the boot sequence and step-by-step execution.
    """

    def __init__(self, provider: ModelProvider | None = None) -> None:
        """Initialize the executor with default handlers.

        Args:
            provider: Optional LLM provider; defaults to StubProvider.
        """
        self.handlers: dict[str, CommandHandler] = self._default_handlers()
        self.provider: ModelProvider = provider or StubProvider()

    def set_provider(self, provider: ModelProvider) -> None:
        """Update the active LLM provider.

        Args:
            provider: The new provider instance.
        """
        self.provider = provider

    def register_handler(self, command: str, handler: CommandHandler) -> None:
        """Register a custom handler for a NODUS command.

        Args:
            command: Command name (e.g., 'CUSTOM_FETCH').
            handler: Callable matching the CommandHandler signature.
        """
        self.handlers[command] = handler

    # ───────────────────────────────────────────────────────────────────────────
    # Public API
    # ───────────────────────────────────────────────────────────────────────────

    def execute(
        self,
        ast: WorkflowFile,
        input_data: dict[str, Any] | None = None,
        global_rules: list[AbsoluteRule] | None = None,
        global_preferences: list[Preference] | None = None,
    ) -> NodusResult:
        """Run a workflow execution cycle.

        Args:
            ast: The parsed WorkflowFile node.
            input_data: Optional initial values for the @in block.

        Returns:
            A populated NodusResult object.
        """
        result = NodusResult()

        if not isinstance(ast, WorkflowFile):
            result.status = "failed"
            result.errors.append(
                {"code": constants.ERR_PARSE_ERROR, "reason": "Expected WorkflowFile"}
            )
            result.ts_end = datetime.now(UTC).isoformat()
            return result

        ctx = ExecutionContext()

        # ── Boot sequence ──────────────────
        if ast.header:
            result.workflow = f"wf:{ast.header.name}"
            result.version = ast.header.version

        # Load Global Rules (Agent System Tape)
        if global_rules:
            ctx.rules.extend(global_rules)
        if global_preferences:
            ctx.preferences.extend(global_preferences)

        # Load Workflow-specific Rules
        ctx.rules.extend(ast.rules)
        ctx.preferences.extend(ast.preferences)

        if input_data:
            ctx.variables["in"] = input_data
            for k, v in input_data.items():
                ctx.variables[k] = v
        elif ast.input_decl:
            defaults: dict[str, Any] = {}
            for field in ast.input_decl.fields:
                if field.default is not None:
                    defaults[field.name] = field.default
            ctx.variables["in"] = defaults

        ctx.variables.setdefault("out", None)
        ctx.variables.setdefault("error", {})
        ctx.variables.setdefault("meta", {})
        ctx.variables.setdefault(
            "session",
            {
                "id": f"session_{int(time.time())}",
                "ts_start": datetime.now(UTC).isoformat(),
                "agent_id": result.agent_id,
                "workflow": result.workflow,
            },
        )
        ctx.variables.setdefault("log", [])
        ctx.variables.setdefault("flags", [])

        # ── Execute @steps ─────────────────
        try:
            for step in ast.steps:
                signal = self._execute_step(ctx, step)
                if signal == "BREAK":
                    if result.status == "ok":
                        result.status = "aborted"
                    break
        except ExecutionError as e:
            ctx.errors.append({"code": e.code, "reason": str(e)})
            result.status = "failed"

        # ── Finalize Result ────────────────
        result.out = ctx.get_var("out")
        result.log = ctx.log
        result.errors = ctx.errors
        result.flags = ctx.flags
        result.ts_end = datetime.now(UTC).isoformat()

        if ctx.errors and result.status == "ok":
            result.status = "partial"

        return result

    # ───────────────────────────────────────────────────────────────────────────
    # Node Execution
    # ───────────────────────────────────────────────────────────────────────────

    def _execute_step(self, ctx: ExecutionContext, step: Step) -> str | None:
        """Execute a numbered step and its sub-steps."""
        if step.body is None:
            return None

        signal = self._execute_node(ctx, step.body, step.number)

        if signal is None:
            for sub in step.sub_steps:
                signal = self._execute_node(ctx, sub, step.number)
                if signal in ("BREAK", "SKIP"):
                    return signal

        return signal

    def _execute_node(
        self, ctx: ExecutionContext, node: Node, step_num: int = 0
    ) -> str | None:
        """Route execution to the specific node type handler."""
        if isinstance(node, CommandCall):
            return self._execute_command(ctx, node, step_num)
        if isinstance(node, Conditional):
            return self._execute_conditional(ctx, node, step_num)
        if isinstance(node, ForLoop):
            return self._execute_for(ctx, node, step_num)
        if isinstance(node, UntilLoop):
            return self._execute_until(ctx, node, step_num)
        if isinstance(node, ParallelBlock):
            return self._execute_parallel(ctx, node, step_num)
        return None

    def _execute_command(
        self, ctx: ExecutionContext, cmd: CommandCall, step_num: int
    ) -> str | None:
        """Execute a validated command call via its handler."""
        violation = ctx.check_rules(cmd.name, cmd.args)
        if violation:
            ctx.errors.append(
                {
                    "code": constants.ERR_RULE_VIOLATION,
                    "step": step_num,
                    "reason": violation,
                }
            )
            raise ExecutionError(constants.ERR_RULE_VIOLATION, violation)

        handler = self.handlers.get(cmd.name)
        if handler is None:
            ctx.flags.append(f"UNKNOWN_COMMAND:{cmd.name}")
            ctx.log_step(step_num, cmd.name, None)
            return None

        result = handler(ctx, cmd)
        ctx.log_step(step_num, cmd.name, result)

        if cmd.pipeline_target:
            ctx.set_var(cmd.pipeline_target, result)

        if cmd.name == "LOG":
            ctx.out_locked = True

        return None

    def _execute_conditional(
        self, ctx: ExecutionContext, cond: Conditional, step_num: int
    ) -> str | None:
        """Process ?IF / ?ELIF / ?ELSE logic."""
        if self._evaluate_condition(ctx, cond.condition):
            if cond.action:
                signal = self._execute_node(ctx, cond.action, step_num)
                if signal:
                    return signal
            if cond.break_flag:
                return "BREAK"
            if cond.skip_flag:
                return "SKIP"
            return None

        for elif_br in cond.elif_branches:
            if self._evaluate_condition(ctx, elif_br.condition):
                if elif_br.action:
                    signal = self._execute_node(ctx, elif_br.action, step_num)
                    if signal:
                        return signal
                if elif_br.break_flag:
                    return "BREAK"
                if elif_br.skip_flag:
                    return "SKIP"
                return None

        if cond.else_branch:
            if cond.else_branch.action:
                signal = self._execute_node(ctx, cond.else_branch.action, step_num)
                if signal:
                    return signal
            if cond.else_branch.break_flag:
                return "BREAK"
            return None

        return None

    def _execute_for(
        self, ctx: ExecutionContext, loop: ForLoop, step_num: int
    ) -> str | None:
        """Process ~FOR iterator over a collection."""
        collection = ctx.get_var(loop.collection)
        if not collection or not isinstance(collection, list):
            return None

        var_name = loop.variable
        for item in collection:
            ctx.set_var(var_name, item)
            for child in loop.body:
                signal = self._execute_node(ctx, child, step_num)
                if signal == "BREAK":
                    return "BREAK"
                if signal == "SKIP":
                    break
        return None

    def _execute_until(
        self, ctx: ExecutionContext, loop: UntilLoop, step_num: int
    ) -> str | None:
        """Process ~UNTIL loop with optional MAX iterations constraint."""
        max_iter = loop.max_iterations or settings.DEFAULT_UNTIL_ITERATIONS
        for _ in range(max_iter):
            for child in loop.body:
                signal = self._execute_node(ctx, child, step_num)
                if signal == "BREAK":
                    return "BREAK"

            if self._evaluate_condition(ctx, loop.condition):
                return None

        ctx.flags.append(constants.ERR_MAX_REACHED)
        return None

    def _execute_parallel(
        self, ctx: ExecutionContext, block: ParallelBlock, step_num: int
    ) -> str | None:
        """Process ~PARALLEL block (Pseudo-implementation)."""
        results: dict[str, Any] = {}
        for branch in block.branches:
            self._execute_node(ctx, branch, step_num)

        if block.join_target:
            ctx.set_var(block.join_target, results)
        return None

    # ───────────────────────────────────────────────────────────────────────────
    # Condition Evaluation
    # ───────────────────────────────────────────────────────────────────────────

    def _evaluate_condition(self, ctx: ExecutionContext, condition: str) -> bool:
        """Compute truth value of a condition string against context variables."""
        if not condition:
            return True

        cond = condition.strip()

        # AND
        if " AND " in cond:
            parts = cond.split(" AND ", 1)
            return self._evaluate_condition(ctx, parts[0]) and self._evaluate_condition(
                ctx, parts[1]
            )

        # OR
        if " OR " in cond:
            parts = cond.split(" OR ", 1)
            return self._evaluate_condition(ctx, parts[0]) or self._evaluate_condition(
                ctx, parts[1]
            )

        # NOT CONTAINS
        if " NOT CONTAINS " in cond:
            parts = cond.split(" NOT CONTAINS ", 1)
            left = self._resolve_value(ctx, parts[0].strip())
            right = self._resolve_value(ctx, parts[1].strip())
            return str(right) not in str(left)

        # CONTAINS
        if " CONTAINS " in cond:
            parts = cond.split(" CONTAINS ", 1)
            left = self._resolve_value(ctx, parts[0].strip())
            right = self._resolve_value(ctx, parts[1].strip())
            if isinstance(left, list):
                return right in left
            return str(right) in str(left)

        # Comparison operators
        for op in ("<=", ">=", "!=", "<", ">", "="):
            if f" {op} " in cond:
                parts = cond.split(f" {op} ", 1)
                left = self._resolve_value(ctx, parts[0].strip())
                right = self._resolve_value(ctx, parts[1].strip())
                return self._compare(left, op, right)

        # Bare value — truthy check
        val = self._resolve_value(ctx, cond)
        return bool(val)

    def _resolve_value(self, ctx: ExecutionContext, expr: str) -> Any:
        """Parse literal or resolve variable name to context value."""
        if expr.startswith("$"):
            return ctx.get_var(expr)
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        try:
            if "." in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass
        if expr == "null":
            return None
        if expr == "true":
            return True
        if expr == "false":
            return False
        return expr

    @staticmethod
    def _compare(left: Any, op: str, right: Any) -> bool:
        """Generic comparison logic for diverse types."""
        try:
            lf = float(left) if left is not None else 0.0
            rf = float(right) if right is not None else 0.0
            if op == "=":
                return lf == rf
            if op == "!=":
                return lf != rf
            if op == "<":
                return lf < rf
            if op == ">":
                return lf > rf
            if op == "<=":
                return lf <= rf
            if op == ">=":
                return lf >= rf
        except (TypeError, ValueError):
            ls, rs = str(left), str(right)
            if op == "=":
                return ls == rs
            if op == "!=":
                return ls != rs
        return False

    # ───────────────────────────────────────────────────────────────────────────
    # Command Handlers
    # ───────────────────────────────────────────────────────────────────────────

    def _default_handlers(self) -> dict[str, CommandHandler]:
        """Dispatch table for core NODUS commands."""
        return {
            "FETCH": self._handle_fetch,
            "ANALYZE": self._handle_analyze,
            "GEN": self._handle_gen,
            "VALIDATE": self._handle_validate,
            "ROUTE": self._handle_route,
            "ESCALATE": self._handle_escalate,
            "LOG": self._handle_log,
            "NOTIFY": self._handle_notify,
            "PUBLISH": self._handle_publish,
            "TONE": self._handle_tone,
            "REFINE": self._handle_refine,
            "SCORE": self._handle_score,
            "APPEND": self._handle_append,
            "MERGE": self._handle_merge,
            "STORE": self._handle_store,
            "LOAD": self._handle_load,
            "COMPARE": self._handle_compare,
            "TRANSLATE": self._handle_translate,
            "SUMMARIZE": self._handle_summarize,
            "WAIT": self._handle_wait,
            "DEBUG": self._handle_debug,
            "QUERY_KB": self._handle_query_kb,
            "REMEMBER": self._handle_remember,
            "RECALL": self._handle_recall,
            "FORGET": self._handle_forget,
            "RUN": self._handle_run,
            "ASSIGN": self._handle_assign,
        }

    @staticmethod
    def _handle_fetch(ctx: ExecutionContext, cmd: CommandCall) -> Any:
        """Simulate content retrieval."""
        _ = ctx
        return {"_stub": True, "source": cmd.args[0] if cmd.args else None}

    def _handle_analyze(self, ctx: ExecutionContext, cmd: CommandCall) -> Any:
        """Perform semantic analysis via the provider."""
        text = ctx.get_var(cmd.args[0]) if cmd.args else ""
        return self.provider.analyze(str(text), cmd.flags)

    def _handle_gen(self, ctx: ExecutionContext, cmd: CommandCall) -> str:
        """Generate content via the LLM provider."""
        prompt = cmd.args[0] if cmd.args else ""
        return self.provider.generate(prompt, cmd.modifiers)

    @staticmethod
    def _handle_validate(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        """Stub validator."""
        return True

    @staticmethod
    def _handle_route(ctx: ExecutionContext, cmd: CommandCall) -> None:
        """Record explicit workflow routing."""
        target = cmd.args[0] if cmd.args else "unknown"
        ctx.flags.append(f"ROUTE:{target}")

    @staticmethod
    def _handle_escalate(ctx: ExecutionContext, cmd: CommandCall) -> None:
        """Record escalation request."""
        target = cmd.args[0] if cmd.args else "human"
        ctx.flags.append(f"ESCALATE:{target}")

    @staticmethod
    def _handle_log(ctx: ExecutionContext, cmd: CommandCall) -> None:
        """Record output to final logs."""
        value = cmd.args[0] if cmd.args else ctx.get_var("out")
        ctx.variables.setdefault("log_entries", []).append(value)

    @staticmethod
    def _handle_notify(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        """Stub notification."""
        _, _ = ctx, cmd
        return True

    @staticmethod
    def _handle_publish(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        """Stub publisher."""
        return True

    @staticmethod
    def _handle_tone(ctx: ExecutionContext, cmd: CommandCall) -> None:
        """Update runtime persona/tone."""
        if cmd.args:
            ctx.active_tone = cmd.args[0]

    @staticmethod
    def _handle_refine(ctx: ExecutionContext, cmd: CommandCall) -> Any:
        """Stub refinement."""
        return ctx.get_var("draft") or settings.STUB_REFINE_TEXT

    @staticmethod
    def _handle_score(ctx: ExecutionContext, cmd: CommandCall) -> float:
        """Stub alignment scoring."""
        return settings.STUB_SCORE_VALUE

    @staticmethod
    def _handle_append(ctx: ExecutionContext, cmd: CommandCall) -> list:
        """Stub list append."""
        return []

    @staticmethod
    def _handle_merge(ctx: ExecutionContext, cmd: CommandCall) -> dict:
        """Merge dictionaries."""
        result: dict[str, Any] = {}
        for arg in cmd.args:
            val = ctx.get_var(arg) if arg.startswith("$") else {}
            if isinstance(val, dict):
                result.update(val)
        return result

    @staticmethod
    def _handle_store(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        """Stub persistent storage."""
        return True

    @staticmethod
    def _handle_load(ctx: ExecutionContext, cmd: CommandCall) -> Any:
        """Stub load."""
        return None

    @staticmethod
    def _handle_compare(ctx: ExecutionContext, cmd: CommandCall) -> dict:
        """Stub comparison."""
        return {"match": False, "diff": {}, "score": 0.0}

    @staticmethod
    def _handle_translate(ctx: ExecutionContext, cmd: CommandCall) -> str:
        """Stub translation."""
        return settings.STUB_TRANSLATE_TEXT

    @staticmethod
    def _handle_summarize(ctx: ExecutionContext, cmd: CommandCall) -> str:
        """Stub summarization."""
        return settings.STUB_SUMMARIZE_TEXT

    @staticmethod
    def _handle_wait(ctx: ExecutionContext, cmd: CommandCall) -> None:
        """Wait (no-op)."""
        pass

    @staticmethod
    def _handle_debug(ctx: ExecutionContext, cmd: CommandCall) -> None:
        """Debug (no-op)."""
        pass

    @staticmethod
    def _handle_query_kb(ctx: ExecutionContext, cmd: CommandCall) -> list:
        """Stub KB query."""
        return []

    @staticmethod
    def _handle_remember(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        """Stub memory storage."""
        return True

    @staticmethod
    def _handle_recall(ctx: ExecutionContext, cmd: CommandCall) -> Any:
        """Stub memory retrieval."""
        return None

    @staticmethod
    def _handle_forget(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        """Stub memory deletion."""
        return True

    @staticmethod
    def _handle_run(ctx: ExecutionContext, cmd: CommandCall) -> Any:
        """Trigger macro execution."""
        macro = cmd.args[0] if cmd.args else "unknown"
        ctx.flags.append(f"RUN:{macro}")
        return None

    @staticmethod
    def _handle_assign(ctx: ExecutionContext, cmd: CommandCall) -> Any:
        """Force assign a value."""
        if len(cmd.args) >= 2:
            ctx.set_var(cmd.args[0], cmd.args[1])
            return cmd.args[1]
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ERRORS
# ═══════════════════════════════════════════════════════════════════════════


class ExecutionError(Exception):
    """Raised when a workflow execution encounters a fatal protocol violation.

    Attributes:
        code: Error code corresponding to constants.
        message: Detailed description of the failure.
    """

    def __init__(self, code: str, message: str):
        """Initialize the error with a code and message."""
        self.code = code
        super().__init__(message)
