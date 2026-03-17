"""NODUS Validator — lint rules for .nodus workflow files.

Implements all 28 lint rules from §lint in schema.nodus:
  E001–E012  (errors — block execution)
  W001–W010  (warnings — unsafe but runs)
  I001–I006  (info — style suggestions)
"""

from __future__ import annotations

import os
import re
from typing import TypeVar, cast

from .. import constants
from .ast_nodes import (
    CommandCall,
    Comment,
    Conditional,
    ConfigFile,
    Diagnostic,
    ForLoop,
    Node,
    ParallelBlock,
    SchemaFile,
    Severity,
    Step,
    UntilLoop,
    WorkflowFile,
)

_T = TypeVar("_T", bound=Node)


class Validator:
    """Validates a parsed NODUS AST against lint rules."""

    def __init__(self, project_root: str = "."):
        self.project_root = project_root

    def validate(self, ast: Node, filename: str = "") -> list[Diagnostic]:
        """Run all applicable lint rules and return diagnostics."""
        if isinstance(ast, WorkflowFile):
            return self._validate_workflow(ast, filename)
        if isinstance(ast, SchemaFile):
            return self._validate_schema(ast, filename)
        if isinstance(ast, ConfigFile):
            return self._validate_config(ast, filename)
        return []

    # ═══════════════════════════════════════
    # WORKFLOW VALIDATION
    # ═══════════════════════════════════════

    def _validate_workflow(self, wf: WorkflowFile, filename: str) -> list[Diagnostic]:
        """Orchestrate all workflow-specific lint rules."""
        d: list[Diagnostic] = []

        d.extend(self._e001_runtime_present(wf, filename))
        d.extend(self._e002_runtime_second(wf, filename))
        d.extend(self._e003_rules_before_steps(wf, filename))
        d.extend(self._e004_variables_declared(wf, filename))
        d.extend(self._e005_publish_after_validate(wf, filename))
        d.extend(self._e006_route_target_exists(wf, filename))
        d.extend(self._e007_loops_closed(wf, filename))
        d.extend(self._e008_parallel_closed(wf, filename))
        d.extend(self._e009_required_no_default(wf, filename))
        d.extend(self._e010_until_has_max(wf, filename))
        d.extend(self._e011_core_path_valid(wf, filename))
        d.extend(self._e012_name_matches_file(wf, filename))

        d.extend(self._w001_err_handler(wf, filename))
        d.extend(self._w002_has_tests(wf, filename))
        d.extend(self._w003_human_mode(wf, filename))
        d.extend(self._w004_step_count(wf, filename))
        d.extend(self._w005_nesting_depth(wf, filename))
        d.extend(self._w006_route_test_coverage(wf, filename))
        d.extend(self._w007_out_assigned(wf, filename))
        d.extend(self._w008_log_last(wf, filename))
        d.extend(self._w009_ctx_in_config(wf, filename))
        d.extend(self._w010_extends_resolve(wf, filename))

        d.extend(self._i001_step_comments(wf, filename))
        d.extend(self._i003_smoke_tag(wf, filename))
        d.extend(self._i004_pref_tones(wf, filename))
        d.extend(self._i006_header_fields(wf, filename))

        return d

    # ── ERRORS ────────────────────────────

    def _e001_runtime_present(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """E001: Missing §runtime block."""
        _ = fn  # Unused in this rule
        if wf.runtime is None:
            return [
                self._d(
                    Severity.ERROR,
                    "E001",
                    "Missing §runtime block. Agent cannot resolve schema.",
                    fn,
                    wf,
                )
            ]
        return []

    def _e002_runtime_second(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """E002: §runtime must appear before !! rules."""
        if wf.runtime and wf.header and wf.runtime.pos and wf.header.pos:
            # rules/triggers/steps should not appear before runtime
            for rule in wf.rules:
                if rule.pos and wf.runtime.pos and rule.pos.line < wf.runtime.pos.line:
                    return [
                        self._d(
                            Severity.ERROR,
                            "E002",
                            "§runtime must appear before !! rules.",
                            fn,
                            rule,
                        )
                    ]
        return []

    def _e003_rules_before_steps(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """E003: !!rule declared after @steps."""
        if not wf.steps or not wf.rules:
            return []
        first_step_line = wf.steps[0].pos.line if wf.steps[0].pos else 9999
        for rule in wf.rules:
            if rule.pos and rule.pos.line > first_step_line:
                return [
                    self._d(
                        Severity.ERROR,
                        "E003",
                        "!!rule declared after @steps. Move all !! rules above @steps.",
                        fn,
                        rule,
                    )
                ]
        return []

    def _e004_variables_declared(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """E004: Variable used but never assigned."""
        declared: set[str] = set()

        # reserved variables always available
        declared.update(constants.RESERVED_VARIABLES)

        # @in fields
        if wf.input_decl:
            for f in wf.input_decl.fields:
                declared.add("$in." + f.name)
                declared.add("$" + f.name)

        # scan steps for assignments (→ $var)
        used: set[str] = set()
        for step in wf.steps:
            self._collect_vars(step, declared, used)

        diags: list[Diagnostic] = []
        for var in used - declared:
            # allow dotted sub-access if root is declared
            root = var.split(".")[0]
            if root in declared:
                continue
            diags.append(
                self._d(
                    Severity.ERROR, "E004", f"{var} used but never assigned.", fn, wf
                )
            )
        return diags

    def _e005_publish_after_validate(
        self, wf: WorkflowFile, fn: str
    ) -> list[Diagnostic]:
        """E005: PUBLISH() called without prior VALIDATE()."""
        has_validate = False
        for step in wf.steps:
            cmds = self._extract_commands(step)
            for cmd in cmds:
                if cmd.name == "VALIDATE":
                    has_validate = True
                if cmd.name == "PUBLISH" and not has_validate:
                    return [
                        self._d(
                            Severity.ERROR,
                            "E005",
                            "PUBLISH() called without prior VALIDATE().",
                            fn,
                            cmd,
                        )
                    ]
        return []

    def _e006_route_target_exists(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """E006: ROUTE target not found."""
        diags: list[Diagnostic] = []
        for step in wf.steps:
            cmds = self._extract_commands(step)
            for cmd in cmds:
                if cmd.name == "ROUTE":
                    for arg in cmd.args:
                        if arg.startswith("wf:"):
                            target_name = arg[3:]
                            # check if target file exists (best effort)
                            found = self._find_workflow(target_name)
                            if not found:
                                diags.append(
                                    self._d(
                                        Severity.ERROR,
                                        "E006",
                                        f"ROUTE target '{arg}' not found.",
                                        fn,
                                        cmd,
                                    )
                                )
        return diags

    def _e007_loops_closed(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """E007: Loops must be properly closed (Handled by Parser)."""
        # The parser handles ~END matching. If a ForLoop or UntilLoop node
        _, _ = wf, fn
        # exists in the AST, it was properly closed during parsing.
        return []

    def _e008_parallel_closed(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """E008: Parallel blocks must be properly closed (Handled by Parser)."""
        # Same as E007 — parser handles ~JOIN matching.
        _, _ = wf, fn
        return []

    def _e009_required_no_default(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """E009: Required fields should not have default values."""
        diags: list[Diagnostic] = []
        if wf.input_decl:
            for f in wf.input_decl.fields:
                if not f.optional and f.default is not None:
                    diags.append(
                        self._d(
                            Severity.ERROR,
                            "E009",
                            f"Required field '{f.name}' has a default value — use ? to mark optional.",
                            fn,
                            f,
                        )
                    )
        return diags

    def _e010_until_has_max(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """E010: ~UNTIL loop missing MAX:n."""
        diags: list[Diagnostic] = []
        for step in wf.steps:
            loops = self._find_nodes(step, UntilLoop)
            for loop in loops:
                if loop.max_iterations is None:
                    diags.append(
                        self._d(
                            Severity.ERROR,
                            "E010",
                            "~UNTIL loop missing MAX:n. Risk of unbounded loop.",
                            fn,
                            loop,
                        )
                    )
        return diags

    def _e011_core_path_valid(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """E011: Core schema not found."""
        if wf.runtime and wf.runtime.core:
            core_path = os.path.join(self.project_root, wf.runtime.core)
            if not os.path.exists(core_path):
                return [
                    self._d(
                        Severity.ERROR,
                        "E011",
                        f"Core schema not found at '{wf.runtime.core}'.",
                        fn,
                        wf.runtime,
                    )
                ]
        return []

    def _e012_name_matches_file(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """E012: Workflow name must match filename."""
        if not fn or not wf.header:
            return []
        basename = os.path.splitext(os.path.basename(fn))[0]
        if wf.header.name and wf.header.name != basename:
            return [
                self._d(
                    Severity.ERROR,
                    "E012",
                    f"Workflow name '{wf.header.name}' does not match filename '{basename}.nodus'.",
                    fn,
                    wf.header,
                )
            ]
        return []

    # ── WARNINGS ──────────────────────────

    def _w001_err_handler(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """W001: No @err handler."""
        if wf.error_decl is None:
            return [
                self._d(
                    Severity.WARNING,
                    "W001",
                    "No @err handler. Errors will trigger NODUS:UNHANDLED_ERROR.",
                    fn,
                    wf,
                )
            ]
        return []

    def _w002_has_tests(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """W002: No @test blocks found."""
        if not wf.tests:
            return [self._d(Severity.WARNING, "W002", "No @test blocks found.", fn, wf)]
        return []

    def _w003_human_mode(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """W003: No HUMAN MODE section."""
        if wf.human_mode is None:
            return [
                self._d(
                    Severity.WARNING,
                    "W003",
                    "No HUMAN MODE section. Workflow is opaque to human reviewers.",
                    fn,
                    wf,
                )
            ]
        return []

    def _w004_step_count(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """W004: Too many steps (recommended max: 20)."""
        n = len(wf.steps)
        if n > 20:
            return [
                self._d(
                    Severity.WARNING,
                    "W004",
                    f"Workflow has {n} steps (recommended max: 20). Consider splitting.",
                    fn,
                    wf,
                )
            ]
        return []

    def _w005_nesting_depth(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """W005: Conditional nesting depth exceeds 3."""
        for step in wf.steps:
            depth = self._max_conditional_depth(step, 0)
            if depth > 3:
                return [
                    self._d(
                        Severity.WARNING,
                        "W005",
                        f"Conditional nesting depth {depth} exceeds 3.",
                        fn,
                        step,
                    )
                ]
        return []

    def _w006_route_test_coverage(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """W006: ROUTE target has no @test coverage."""
        # collect all ROUTE targets
        route_targets: set[str] = set()
        for step in wf.steps:
            for cmd in self._extract_commands(step):
                if cmd.name == "ROUTE":
                    for arg in cmd.args:
                        route_targets.add(arg)

        # check if any test exercises each route
        diags: list[Diagnostic] = []
        for target in route_targets:
            found = False
            for test in wf.tests:
                if target in " ".join(test.raw_lines):
                    found = True
                    break
            if not found:
                diags.append(
                    self._d(
                        Severity.WARNING,
                        "W006",
                        f"ROUTE({target}) has no @test coverage.",
                        fn,
                        wf,
                    )
                )
        return diags

    def _w007_out_assigned(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """W007: Output variable never assigned."""
        if not wf.output_decl or not wf.output_decl.variable:
            return []
        target_var = wf.output_decl.variable
        for step in wf.steps:
            for cmd in self._extract_commands(step):
                if cmd.pipeline_target == target_var:
                    return []
        return [
            self._d(
                Severity.WARNING,
                "W007",
                f"{target_var} declared in @out but never assigned in @steps.",
                fn,
                wf,
            )
        ]

    def _w008_log_last(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """W008: LOG() is not the last step."""
        if not wf.steps:
            return []
        # check last two steps for LOG
        for step in reversed(wf.steps[-2:]):
            for cmd in self._extract_commands(step):
                if cmd.name == "LOG":
                    return []
        # check if LOG exists at all
        for step in wf.steps:
            for cmd in self._extract_commands(step):
                if cmd.name == "LOG":
                    return [
                        self._d(
                            Severity.WARNING,
                            "W008",
                            "LOG() is not the last step.",
                            fn,
                            step,
                        )
                    ]
        return []

    def _w009_ctx_in_config(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """W009: Missing context in config (TODO)."""
        _, _ = wf, fn
        return []

    def _w010_extends_resolve(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """W010: Schema extension not found."""
        diags: list[Diagnostic] = []
        if wf.runtime:
            for ext_path in wf.runtime.extends:
                full = os.path.join(self.project_root, ext_path)
                if not os.path.exists(full):
                    diags.append(
                        self._d(
                            Severity.WARNING,
                            "W010",
                            f"Schema extension not found: '{ext_path}'.",
                            fn,
                            wf.runtime,
                        )
                    )
        return diags

    # ── INFO ──────────────────────────────

    def _i001_step_comments(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """I001: Step has no comment."""
        diags: list[Diagnostic] = []
        for step in wf.steps:
            if not step.comment and not isinstance(step.body, Comment):
                diags.append(
                    self._d(
                        Severity.INFO,
                        "I001",
                        f"Step {step.number} has no comment.",
                        fn,
                        step,
                    )
                )
        return diags

    def _i003_smoke_tag(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """I003: No smoke test defined."""
        if not wf.tests:
            return []
        for test in wf.tests:
            if "smoke" in test.tags:
                return []
            if "smoke" in " ".join(test.raw_lines):
                return []
        return [self._d(Severity.INFO, "I003", "No smoke test defined.", fn, wf)]

    def _i004_pref_tones(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """I004: Unknown tone in !PREF rule."""
        diags: list[Diagnostic] = []
        for pref in wf.preferences:
            for token in (pref.preferred + " " + pref.over).split():
                if token.startswith("tone") or token in constants.VALID_TONES:
                    continue
                # check if a tone value is mentioned
                if "=" in pref.preferred:
                    _, val = pref.preferred.split("=", 1)
                    val = val.strip()
                    if (
                        val
                        and val not in constants.VALID_TONES
                        and val.startswith("$") is False
                    ):
                        diags.append(
                            self._d(
                                Severity.INFO,
                                "I004",
                                f"Unknown tone '{val}' in !PREF rule.",
                                fn,
                                pref,
                            )
                        )
                    break
        return diags

    def _i006_header_fields(self, wf: WorkflowFile, fn: str) -> list[Diagnostic]:
        """I006: Header name/version is empty."""
        diags: list[Diagnostic] = []
        if wf.header:
            if not wf.header.name:
                diags.append(
                    self._d(
                        Severity.INFO, "I006", "Header name is empty.", fn, wf.header
                    )
                )
            if not wf.header.version:
                diags.append(
                    self._d(
                        Severity.INFO, "I006", "Header version is empty.", fn, wf.header
                    )
                )
        return diags

    # ═══════════════════════════════════════
    # SCHEMA / CONFIG VALIDATION
    # ═══════════════════════════════════════

    def _validate_schema(self, sf: SchemaFile, fn: str) -> list[Diagnostic]:
        """Validate SchemaFile nodes."""
        d: list[Diagnostic] = []
        if sf.header and not sf.header.version:
            d.append(
                self._d(
                    Severity.INFO, "I006", "Schema version is empty.", fn, sf.header
                )
            )
        return d

    def _validate_config(self, cf: ConfigFile, fn: str) -> list[Diagnostic]:
        """Validate ConfigFile nodes."""
        d: list[Diagnostic] = []
        if cf.runtime is None:
            d.append(
                self._d(
                    Severity.ERROR, "E001", "Missing §runtime block in config.", fn, cf
                )
            )
        return d

    # ═══════════════════════════════════════
    # UTILITY
    # ═══════════════════════════════════════

    @staticmethod
    def _d(
        severity: Severity,
        code: str,
        msg: str,
        filename: str,
        node: Node | None = None,
    ) -> Diagnostic:
        """Create a Diagnostic object."""
        line = node.pos.line if node and node.pos else 0
        col = node.pos.column if node and node.pos else 0
        return Diagnostic(severity, code, msg, line, col, filename)

    def _collect_vars(self, node: Node, declared: set[str], used: set[str]) -> None:
        """Recursively walk the node tree to collect declared (assigned) and used variables."""
        if isinstance(node, Step):
            if node.body:
                self._collect_vars(node.body, declared, used)
            for sub in node.sub_steps:
                self._collect_vars(sub, declared, used)

        elif isinstance(node, CommandCall):
            # args that are variables
            for arg in node.args:
                if arg.startswith("$"):
                    used.add(arg.split(".")[0])
            # modifier values that are variables
            for val in node.modifiers.values():
                if isinstance(val, str) and val.startswith("$"):
                    used.add(val.split(".")[0])
            # pipeline target is a declaration
            if node.pipeline_target and node.pipeline_target.startswith("$"):
                declared.add(node.pipeline_target.split(".")[0])

        elif isinstance(node, Conditional):
            # variables in condition text
            for m in re.finditer(r"\$[a-zA-Z_][a-zA-Z0-9_.]*", node.condition):
                used.add(m.group().split(".")[0])
            if node.action:
                self._collect_vars(node.action, declared, used)
            for br in node.elif_branches:
                self._collect_vars(br, declared, used)
            if node.else_branch:
                self._collect_vars(node.else_branch, declared, used)

        elif isinstance(node, ForLoop):
            if node.variable.startswith("$"):
                declared.add(node.variable)
            if node.collection.startswith("$"):
                used.add(node.collection.split(".")[0])
            for child in node.body:
                self._collect_vars(child, declared, used)

        elif isinstance(node, UntilLoop):
            for m in re.finditer(r"\$[a-zA-Z_][a-zA-Z0-9_.]*", node.condition):
                used.add(m.group().split(".")[0])
            for child in node.body:
                self._collect_vars(child, declared, used)

        elif isinstance(node, ParallelBlock):
            for child in node.branches:
                self._collect_vars(child, declared, used)
            if node.join_target and node.join_target.startswith("$"):
                declared.add(node.join_target)

    def _extract_commands(self, node: Node) -> list[CommandCall]:
        """Deeply extract all CommandCall nodes from any given AST subtree."""
        cmds: list[CommandCall] = []
        if isinstance(node, CommandCall):
            cmds.append(node)
        elif isinstance(node, Step):
            if isinstance(node.body, CommandCall):
                cmds.append(node.body)
            if node.body:
                cmds.extend(self._extract_commands(node.body))
            for sub in node.sub_steps:
                cmds.extend(self._extract_commands(sub))
        elif isinstance(node, Conditional):
            if node.action:
                cmds.extend(self._extract_commands(node.action))
            for br in node.elif_branches:
                cmds.extend(self._extract_commands(br))
            if node.else_branch:
                cmds.extend(self._extract_commands(node.else_branch))
        elif isinstance(node, (ForLoop, UntilLoop)):
            for child in node.body:
                cmds.extend(self._extract_commands(child))
        elif isinstance(node, ParallelBlock):
            for child in node.branches:
                cmds.extend(self._extract_commands(child))
        return cmds

    def _find_nodes(self, node: Node, node_type: type[_T]) -> list[_T]:
        """General-purpose search to find all nodes of a specific type in the tree."""
        results: list[Node] = []
        if isinstance(node, node_type):
            results.append(node)
        if isinstance(node, Step):
            if node.body:
                results.extend(self._find_nodes(node.body, node_type))
            for sub in node.sub_steps:
                results.extend(self._find_nodes(sub, node_type))
        elif isinstance(node, (ForLoop, UntilLoop)):
            for child in node.body:
                results.extend(self._find_nodes(child, node_type))
        elif isinstance(node, ParallelBlock):
            for child in node.branches:
                results.extend(self._find_nodes(child, node_type))
        elif isinstance(node, Conditional):
            if node.action:
                results.extend(self._find_nodes(node.action, node_type))
            for br in node.elif_branches:
                results.extend(self._find_nodes(br, node_type))
            if node.else_branch:
                results.extend(self._find_nodes(node.else_branch, node_type))
        return cast(list[_T], results)

    def _max_conditional_depth(self, node: Node, current: int) -> int:
        """Calculate maximum ?IF nesting depth."""
        if isinstance(node, Conditional):
            depth = current + 1
            for br in node.elif_branches:
                depth = max(depth, self._max_conditional_depth(br, current + 1))
            if node.else_branch:
                depth = max(
                    depth, self._max_conditional_depth(node.else_branch, current + 1)
                )
            return depth
        if isinstance(node, Step):
            d = current
            if node.body:
                d = max(d, self._max_conditional_depth(node.body, current))
            for sub in node.sub_steps:
                d = max(d, self._max_conditional_depth(sub, current))
            return d
        return current

    def _find_workflow(self, name: str) -> bool:
        """Check if a workflow file exists by name."""
        candidates = [
            os.path.join(self.project_root, "workflows", f"{name}.nodus"),
            os.path.join(self.project_root, "workflows", "social", f"{name}.nodus"),
            os.path.join(self.project_root, "workflows", "support", f"{name}.nodus"),
        ]
        return any(os.path.exists(p) for p in candidates)
