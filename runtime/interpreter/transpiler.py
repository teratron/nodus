"""NODUS Transpiler — converts between NODUS mode and HUMAN mode.

NODUS mode  →  machine-optimized symbolic syntax
HUMAN mode  →  plain-language readable description

Both represent the same workflow logic. The transpiler converts
a parsed AST into either representation.
"""

from __future__ import annotations

from typing import List

from .ast_nodes import (
    CommandCall,
    Comment,
    Conditional,
    ForLoop,
    ParallelBlock,
    Step,
    UntilLoop,
    WorkflowFile,
)


class Transpiler:
    """Converts NODUS AST between NODUS and HUMAN representations."""

    # ═══════════════════════════════════════
    # NODUS → HUMAN
    # ═══════════════════════════════════════

    def to_human(self, ast: WorkflowFile) -> str:
        """Convert a parsed workflow AST to HUMAN mode text."""
        lines: List[str] = []

        # Header
        if ast.header:
            lines.append(f"WORKFLOW: {ast.header.name}")
        lines.append("")

        # Triggers
        if ast.triggers:
            triggers_desc = ", ".join(
                self._humanize_trigger(t.condition) for t in ast.triggers
            )
            lines.append(f"TRIGGER: {triggers_desc}")
            lines.append("")

        # Input
        if ast.input_decl and ast.input_decl.fields:
            parts: List[str] = []
            for f in ast.input_decl.fields:
                desc = f.name
                if f.optional and f.default:
                    desc += f" (default: {f.default})"
                elif f.optional:
                    desc += " (optional)"
                parts.append(desc)
            lines.append(f"INPUT: {', '.join(parts)}")

        # Context
        if ast.context_decl and ast.context_decl.contexts:
            lines.append(f"CONTEXT: load {', '.join(ast.context_decl.contexts)}")

        lines.append("")

        # Rules
        if ast.rules or ast.preferences:
            lines.append("RULES:")
            for rule in ast.rules:
                lines.append(
                    f"  - {rule.rule_type} {self._humanize_rule(rule.content)}"
                )
            for pref in ast.preferences:
                desc = f"Prefer {pref.preferred} over {pref.over}"
                if pref.condition:
                    desc += f" if {pref.condition}"
                lines.append(f"  - {desc}")
            lines.append("")

        # Steps
        if ast.steps:
            lines.append("STEPS:")
            for step in ast.steps:
                desc = self._humanize_step(step)
                if desc:
                    lines.append(f"  {step.number}. {desc}")
            lines.append("")

        # Output
        if ast.output_decl:
            lines.append(f"OUTPUT: {self._humanize_var(ast.output_decl.variable)}")

        # Error
        if ast.error_decl:
            lines.append(f"ON ERROR: {self._humanize_error(ast.error_decl.raw)}")

        return "\n".join(lines)

    # ═══════════════════════════════════════
    # HUMAN → NODUS
    # ═══════════════════════════════════════

    def to_nodus(self, ast: WorkflowFile) -> str:
        """Convert a parsed workflow AST back to NODUS mode text."""
        lines: List[str] = []

        # Header
        if ast.header:
            lines.append(f"\u00a7wf:{ast.header.name} {ast.header.version}")

        # Runtime
        if ast.runtime:
            lines.append("\u00a7runtime: {")
            lines.append(f"  core:    {ast.runtime.core}")
            if ast.runtime.extends:
                ext = ", ".join(ast.runtime.extends)
                lines.append(f"  extends: [{ext}]")
            if ast.runtime.agents:
                agent_parts = ", ".join(
                    f"{k}: {v}" for k, v in ast.runtime.agents.items()
                )
                lines.append(f"  agents:  {{ {agent_parts} }}")
            lines.append(f"  mode:    {ast.runtime.mode}")
            lines.append("}")

        # Triggers
        for trigger in ast.triggers:
            lines.append(f"@ON: {trigger.condition} \u2192 {trigger.action}")

        lines.append("")

        # Rules
        for rule in ast.rules:
            lines.append(f"!!{rule.rule_type}: {rule.content}")
        for pref in ast.preferences:
            line = f"!PREF: {pref.preferred} OVER {pref.over}"
            if pref.condition:
                line += f" IF {pref.condition}"
            lines.append(line)

        lines.append("")

        # Declarations
        if ast.input_decl:
            fields: List[str] = []
            for f in ast.input_decl.fields:
                decl = f.name
                if f.optional:
                    decl += "?"
                if f.type_name and f.type_name != "any":
                    decl += f": {f.type_name}"
                if f.default:
                    decl += f" = {f.default}"
                fields.append(decl)
            lines.append(f"@in: {{ {', '.join(fields)} }}")

        if ast.context_decl:
            lines.append(f"@ctx: [{', '.join(ast.context_decl.contexts)}]")

        if ast.output_decl:
            lines.append(f"@out: {ast.output_decl.variable}")

        if ast.error_decl:
            lines.append(f"@err: {ast.error_decl.raw}")

        lines.append("")

        # Steps
        if ast.steps:
            lines.append("@steps:")
            for step in ast.steps:
                nodus_line = self._nodus_step(step)
                if nodus_line:
                    lines.append(f"  {step.number}. {nodus_line}")

        # Tests
        for test in ast.tests:
            lines.append("")
            lines.append(f"@test:{test.name} {{")
            for raw in test.raw_lines:
                lines.append(f"  {raw}")
            lines.append("}")

        return "\n".join(lines)

    # ═══════════════════════════════════════
    # HUMANIZERS
    # ═══════════════════════════════════════

    def _humanize_trigger(self, condition: str) -> str:
        cond = condition.strip()
        if cond.startswith("new_"):
            return f"when a {cond.replace('_', ' ')} is received"
        if "schedule:" in cond:
            time = cond.split("schedule:", 1)[1].strip()
            return f"every day at {time}"
        if "webhook:" in cond:
            hook = cond.split("webhook:", 1)[1].strip()
            return f"when {hook.replace('_', ' ')} webhook fires"
        if "CONTAINS" in cond:
            return f"when {cond.lower()}"
        return f"when {cond}"

    def _humanize_rule(self, content: str) -> str:
        content = content.lower()
        content = content.replace("$out", "the output")
        content = content.replace("$error.level", "error level")
        return content

    def _humanize_step(self, step: Step) -> str:
        if step.comment:
            # use comment as description
            text = step.comment.lstrip(";").strip()
            if text.startswith("—"):
                text = text.lstrip("—").strip()
            return text

        if isinstance(step.body, CommandCall):
            return self._humanize_command(step.body)
        if isinstance(step.body, Conditional):
            return self._humanize_conditional(step.body)
        if isinstance(step.body, ForLoop):
            return self._humanize_for(step.body)
        if isinstance(step.body, UntilLoop):
            return self._humanize_until(step.body)
        if isinstance(step.body, ParallelBlock):
            return "Run the following in parallel"
        if isinstance(step.body, Comment):
            text = step.body.text.lstrip(";").strip()
            return text if text else ""
        return ""

    def _humanize_command(self, cmd: CommandCall) -> str:
        name = cmd.name
        args = ", ".join(cmd.args)

        _VERB_MAP = {
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

        verb = _VERB_MAP.get(name, name)
        desc = f"{verb} {args}" if args else verb

        if cmd.flags:
            desc += f" (extract: {', '.join(cmd.flags)})"
        if cmd.validators:
            rules = ", ".join(v.lstrip("^") for v in cmd.validators)
            desc += f" against rules: {rules}"
        if cmd.pipeline_target:
            desc += f" → store as {self._humanize_var(cmd.pipeline_target)}"
        return desc

    def _humanize_conditional(self, cond: Conditional) -> str:
        desc = f"IF {cond.condition}"
        if cond.action and isinstance(cond.action, CommandCall):
            desc += f" → {self._humanize_command(cond.action)}"
        if cond.break_flag:
            desc += ", STOP"
        return desc

    def _humanize_for(self, loop: ForLoop) -> str:
        return f"For each {self._humanize_var(loop.variable)} in {self._humanize_var(loop.collection)}"

    def _humanize_until(self, loop: UntilLoop) -> str:
        desc = f"Repeat until {loop.condition}"
        if loop.max_iterations:
            desc += f" (max {loop.max_iterations} attempts)"
        return desc

    def _humanize_var(self, var: str) -> str:
        if not var:
            return ""
        return var.lstrip("$").replace(".", " → ")

    def _humanize_error(self, raw: str) -> str:
        if "ESCALATE" in raw and "human" in raw.lower():
            return "escalate to human"
        return raw

    # ═══════════════════════════════════════
    # NODUS RECONSTRUCTORS
    # ═══════════════════════════════════════

    def _nodus_step(self, step: Step) -> str:
        if isinstance(step.body, CommandCall):
            return self._nodus_command(step.body)
        if isinstance(step.body, Comment):
            return f";; {step.body.text}"
        if step.comment:
            return f";; {step.comment}"
        return ""

    def _nodus_command(self, cmd: CommandCall) -> str:
        parts = [f"{cmd.name}({', '.join(cmd.args)})"]
        for mod_name, mod_val in cmd.modifiers.items():
            if mod_val:
                parts.append(f"{mod_name}={mod_val}")
            else:
                parts.append(mod_name)
        for v in cmd.validators:
            parts.append(v)
        for f in cmd.flags:
            parts.append(f"~{f}")
        if cmd.pipeline_target:
            parts.append(f"\u2192 {cmd.pipeline_target}")
        return " ".join(parts)
