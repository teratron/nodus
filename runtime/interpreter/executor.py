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

import time
import abc
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

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


# Type alias for command handler functions
CommandHandler = Callable[["ExecutionContext", CommandCall], Any]


class ModelProvider(abc.ABC):
    """Abstract base class for LLM providers."""

    @abc.abstractmethod
    def generate(self, prompt: str, modifiers: Dict[str, Any]) -> str:
        """Generate text."""
        ...

    @abc.abstractmethod
    def analyze(self, text: str, flags: List[str]) -> Dict[str, Any]:
        """Analyze text."""
        ...


class StubProvider(ModelProvider):
    """Default provider that returns stubs."""

    def generate(self, prompt: str, modifiers: Dict[str, Any]) -> str:
        tone = modifiers.get("+tone", "brand")
        return f"[Generated {prompt} in {tone} tone (STUB)]"

    def analyze(self, text: str, flags: List[str]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for flag in flags:
            result[flag] = "mock_value" if flag == "intent" else 0.5
        return result


class AnthropicProvider(ModelProvider):
    """Example provider for Anthropic Claude (Stubbed for now)."""

    def generate(self, prompt: str, modifiers: Dict[str, Any]) -> str:
        # TODO: Implement real call to anthropic-sdk
        return f"[Generated via ANTHROPIC: {prompt}]"

    def analyze(self, text: str, flags: List[str]) -> Dict[str, Any]:
        return {"intent": "analyzed_by_anthropic", "sentiment": 0.9}


class ExecutionContext:
    """Runtime state for a single workflow execution."""

    def __init__(self) -> None:
        self.variables: Dict[str, Any] = {}
        self.rules: List[AbsoluteRule] = []
        self.preferences: List[Preference] = []
        self.log: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.flags: List[str] = []
        self.active_tone: str = "brand"
        self.out_locked: bool = False

    def set_var(self, name: str, value: Any) -> None:
        """Set a variable. Respects $out lock after LOG."""
        clean = name.lstrip("$")
        if clean == "out" and self.out_locked:
            self.errors.append(
                {
                    "code": "NODUS:RULE_VIOLATION",
                    "reason": "Cannot modify $out after LOG() has been called.",
                }
            )
            return
        self.variables[clean] = value

    def get_var(self, name: str) -> Any:
        """Get a variable by name (with or without $ prefix)."""
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
        """Log a workflow step execution."""
        self.log.append(
            {
                "step": step_num,
                "command": command,
                "result": result,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        )

    def check_rules(self, command: str, args: List[str]) -> Optional[str]:
        """Check if a command violates any !! rules. Returns violation message or None."""
        _ = args  # Unused for now
        cmd_lower = command.lower()

        for rule in self.rules:
            content_lower = rule.content.lower()
            if rule.rule_type == "NEVER":
                # "publish WITHOUT validate"
                _ = args  # Unused in this check
                if "publish" in content_lower and cmd_lower == "publish":
                    if "without" in content_lower and "validate" in content_lower:
                        # check if validate was called
                        validated = any(
                            e.get("command") == "VALIDATE" for e in self.log
                        )
                        if not validated:
                            return f"!!NEVER: {rule.content}"
            elif rule.rule_type == "ALWAYS":
                pass  # ALWAYS rules are checked post-execution

        return None


class NodusResult:
    """NODUS:RESULT — the standard output of every workflow execution."""

    def __init__(self) -> None:
        self.workflow: str = ""
        self.version: str = ""
        self.status: str = "ok"  # ok | partial | failed | aborted
        self.out: Any = None
        self.log: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.flags: List[str] = []
        self.ts_end: str = ""
        self.agent_id: str = "nodus-executor"

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a dictionary."""
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


class Executor:
    """Executes a parsed NODUS workflow AST."""

    def __init__(self, provider: Optional[ModelProvider] = None) -> None:
        self.handlers: Dict[str, CommandHandler] = self._default_handlers()
        self.provider: ModelProvider = provider or StubProvider()

    def set_provider(self, provider: ModelProvider) -> None:
        """Set the active LLM provider."""
        self.provider = provider

    def register_handler(self, command: str, handler: CommandHandler) -> None:
        """Register a custom command handler."""
        self.handlers[command] = handler

    # ═══════════════════════════════════════
    # PUBLIC
    # ═══════════════════════════════════════

    def execute(
        self,
        ast: WorkflowFile,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> NodusResult:
        """Execute a workflow and return NODUS:RESULT."""
        result = NodusResult()

        if not isinstance(ast, WorkflowFile):
            result.status = "failed"
            result.errors.append(
                {"code": "NODUS:PARSE_ERROR", "reason": "Expected WorkflowFile"}
            )
            result.ts_end = datetime.now(timezone.utc).isoformat()
            return result

        ctx = ExecutionContext()

        # ── Boot sequence ──────────────────
        # 1. Header
        if ast.header:
            result.workflow = f"wf:{ast.header.name}"
            result.version = ast.header.version

        # 2. Load !! rules
        ctx.rules = list(ast.rules)

        # 3. Load !PREF preferences
        ctx.preferences = list(ast.preferences)

        # 4. Load @in
        if input_data:
            ctx.variables["in"] = input_data
            for k, v in input_data.items():
                ctx.variables[k] = v
        elif ast.input_decl:
            defaults: Dict[str, Any] = {}
            for field in ast.input_decl.fields:
                if field.default is not None:
                    defaults[field.name] = field.default
            ctx.variables["in"] = defaults

        # 5. Initialize reserved variables
        ctx.variables.setdefault("out", None)
        ctx.variables.setdefault("error", {})
        ctx.variables.setdefault("meta", {})
        ctx.variables.setdefault(
            "session",
            {
                "id": f"session_{int(time.time())}",
                "ts_start": datetime.now(timezone.utc).isoformat(),
                "agent_id": result.agent_id,
                "workflow": result.workflow,
            },
        )
        ctx.variables.setdefault("log", [])
        ctx.variables.setdefault("flags", [])

        # 6. Execute @steps
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

        # ── Build result ───────────────────
        result.out = ctx.get_var("out")
        result.log = ctx.log
        result.errors = ctx.errors
        result.flags = ctx.flags
        result.ts_end = datetime.now(timezone.utc).isoformat()

        if ctx.errors and result.status == "ok":
            result.status = "partial"

        return result

    # ═══════════════════════════════════════
    # STEP EXECUTION
    # ═══════════════════════════════════════

    def _execute_step(self, ctx: ExecutionContext, step: Step) -> Optional[str]:
        """Execute a single step. Returns 'BREAK' or 'SKIP' or None."""
        if step.body is None:
            return None

        signal = self._execute_node(ctx, step.body, step.number)

        # execute sub-steps
        if signal is None:
            for sub in step.sub_steps:
                signal = self._execute_node(ctx, sub, step.number)
                if signal in ("BREAK", "SKIP"):
                    return signal

        return signal

    def _execute_node(
        self, ctx: ExecutionContext, node: Node, step_num: int = 0
    ) -> Optional[str]:
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
    ) -> Optional[str]:
        # Check !! rules
        violation = ctx.check_rules(cmd.name, cmd.args)
        if violation:
            ctx.errors.append(
                {
                    "code": "NODUS:RULE_VIOLATION",
                    "step": step_num,
                    "reason": violation,
                }
            )
            raise ExecutionError("NODUS:RULE_VIOLATION", violation)

        # Dispatch to handler
        handler = self.handlers.get(cmd.name)
        if handler is None:
            ctx.flags.append(f"UNKNOWN_COMMAND:{cmd.name}")
            ctx.log_step(step_num, cmd.name, None)
            return None

        result = handler(ctx, cmd)
        ctx.log_step(step_num, cmd.name, result)

        # Assign to pipeline target
        if cmd.pipeline_target:
            ctx.set_var(cmd.pipeline_target, result)

        # Special: LOG locks $out
        if cmd.name == "LOG":
            ctx.out_locked = True

        return None

    def _execute_conditional(
        self, ctx: ExecutionContext, cond: Conditional, step_num: int
    ) -> Optional[str]:
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
    ) -> Optional[str]:
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
    ) -> Optional[str]:
        max_iter = loop.max_iterations or 5
        for _ in range(max_iter):
            for child in loop.body:
                signal = self._execute_node(ctx, child, step_num)
                if signal == "BREAK":
                    return "BREAK"

            if self._evaluate_condition(ctx, loop.condition):
                return None

        ctx.flags.append("NODUS:MAX_REACHED")
        return None

    def _execute_parallel(
        self, ctx: ExecutionContext, block: ParallelBlock, step_num: int
    ) -> Optional[str]:
        # In a real implementation, branches would run concurrently.
        # Here we execute sequentially for simplicity.
        results: Dict[str, Any] = {}
        for branch in block.branches:
            self._execute_node(ctx, branch, step_num)

        if block.join_target:
            ctx.set_var(block.join_target, results)
        return None

    # ═══════════════════════════════════════
    # CONDITION EVALUATOR
    # ═══════════════════════════════════════

    def _evaluate_condition(self, ctx: ExecutionContext, condition: str) -> bool:
        """Evaluate a condition string against the current context.

        Supports: <, >, <=, >=, =, !=, CONTAINS, NOT, AND, OR
        """
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
        """Resolve an expression to a value."""
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
        # identifiers like 'null', 'true', 'false'
        if expr == "null":
            return None
        if expr == "true":
            return True
        if expr == "false":
            return False
        return expr

    @staticmethod
    def _compare(left: Any, op: str, right: Any) -> bool:
        # Try numeric comparison first
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
            # Fall back to string comparison
            ls, rs = str(left), str(right)
            if op == "=":
                return ls == rs
            if op == "!=":
                return ls != rs
        return False

    # ═══════════════════════════════════════
    # DEFAULT HANDLERS (stubs)
    # ═══════════════════════════════════════

    def _default_handlers(self) -> Dict[str, CommandHandler]:
        """Return default stub handlers for all core commands."""
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
        _ = ctx
        return {"_stub": True, "source": cmd.args[0] if cmd.args else None}

    def _handle_analyze(self, ctx: ExecutionContext, cmd: CommandCall) -> Any:
        text = ctx.get_var(cmd.args[0]) if cmd.args else ""
        return self.provider.analyze(str(text), cmd.flags)

    def _handle_gen(self, ctx: ExecutionContext, cmd: CommandCall) -> str:
        prompt = cmd.args[0] if cmd.args else ""
        return self.provider.generate(prompt, cmd.modifiers)

    @staticmethod
    def _handle_validate(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        return True

    @staticmethod
    def _handle_route(ctx: ExecutionContext, cmd: CommandCall) -> None:
        target = cmd.args[0] if cmd.args else "unknown"
        ctx.flags.append(f"ROUTE:{target}")

    @staticmethod
    def _handle_escalate(ctx: ExecutionContext, cmd: CommandCall) -> None:
        target = cmd.args[0] if cmd.args else "human"
        ctx.flags.append(f"ESCALATE:{target}")

    @staticmethod
    def _handle_log(ctx: ExecutionContext, cmd: CommandCall) -> None:
        value = cmd.args[0] if cmd.args else ctx.get_var("out")
        ctx.variables.setdefault("log_entries", []).append(value)

    @staticmethod
    def _handle_notify(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        _, _ = ctx, cmd
        return True

    @staticmethod
    def _handle_publish(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        return True

    @staticmethod
    def _handle_tone(ctx: ExecutionContext, cmd: CommandCall) -> None:
        if cmd.args:
            ctx.active_tone = cmd.args[0]

    @staticmethod
    def _handle_refine(ctx: ExecutionContext, cmd: CommandCall) -> Any:
        return ctx.get_var("draft") or "[Refined content]"

    @staticmethod
    def _handle_score(ctx: ExecutionContext, cmd: CommandCall) -> float:
        return 0.85

    @staticmethod
    def _handle_append(ctx: ExecutionContext, cmd: CommandCall) -> list:
        return []

    @staticmethod
    def _handle_merge(ctx: ExecutionContext, cmd: CommandCall) -> dict:
        result: Dict[str, Any] = {}
        for arg in cmd.args:
            val = ctx.get_var(arg) if arg.startswith("$") else {}
            if isinstance(val, dict):
                result.update(val)
        return result

    @staticmethod
    def _handle_store(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        return True

    @staticmethod
    def _handle_load(ctx: ExecutionContext, cmd: CommandCall) -> Any:
        return None

    @staticmethod
    def _handle_compare(ctx: ExecutionContext, cmd: CommandCall) -> dict:
        return {"match": False, "diff": {}, "score": 0.0}

    @staticmethod
    def _handle_translate(ctx: ExecutionContext, cmd: CommandCall) -> str:
        return "[Translated content]"

    @staticmethod
    def _handle_summarize(ctx: ExecutionContext, cmd: CommandCall) -> str:
        return "[Summary]"

    @staticmethod
    def _handle_wait(ctx: ExecutionContext, cmd: CommandCall) -> None:
        pass

    @staticmethod
    def _handle_debug(ctx: ExecutionContext, cmd: CommandCall) -> None:
        pass

    @staticmethod
    def _handle_query_kb(ctx: ExecutionContext, cmd: CommandCall) -> list:
        return []

    @staticmethod
    def _handle_remember(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        return True

    @staticmethod
    def _handle_recall(ctx: ExecutionContext, cmd: CommandCall) -> Any:
        return None

    @staticmethod
    def _handle_forget(ctx: ExecutionContext, cmd: CommandCall) -> bool:
        return True

    @staticmethod
    def _handle_run(ctx: ExecutionContext, cmd: CommandCall) -> Any:
        macro = cmd.args[0] if cmd.args else "unknown"
        ctx.flags.append(f"RUN:{macro}")
        return None

    @staticmethod
    def _handle_assign(ctx: ExecutionContext, cmd: CommandCall) -> Any:
        if len(cmd.args) >= 2:
            ctx.set_var(cmd.args[0], cmd.args[1])
            return cmd.args[1]
        return None


class ExecutionError(Exception):
    """Raised when a workflow execution encounters a fatal error."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)
