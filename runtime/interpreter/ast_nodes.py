"""NODUS Abstract Syntax Tree node definitions.

Every parsed .nodus file is represented as a tree of these nodes.
Position information is attached for error reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


# ─────────────────────────────────────────────
# POSITION
# ─────────────────────────────────────────────


@dataclass
class Position:
    """Source location for error reporting."""

    line: int
    column: int = 0
    filename: str = ""

    def __str__(self) -> str:
        loc = f"{self.line}:{self.column}"
        return f"{self.filename}:{loc}" if self.filename else loc


# ─────────────────────────────────────────────
# BASE NODE
# ─────────────────────────────────────────────


@dataclass
class Node:
    """Base class for all AST nodes."""

    pos: Optional[Position] = field(default=None, repr=False)


# ─────────────────────────────────────────────
# FILE-LEVEL NODES
# ─────────────────────────────────────────────


@dataclass
class WorkflowFile(Node):
    """Top-level node for a .nodus workflow file."""

    header: Optional[FileHeader] = None
    runtime: Optional[RuntimeBlock] = None
    triggers: List[Trigger] = field(default_factory=list)
    rules: List[AbsoluteRule] = field(default_factory=list)
    preferences: List[Preference] = field(default_factory=list)
    input_decl: Optional[InputDecl] = None
    output_decl: Optional[OutputDecl] = None
    context_decl: Optional[ContextDecl] = None
    error_decl: Optional[ErrorDecl] = None
    steps: List[Step] = field(default_factory=list)
    tests: List[TestBlock] = field(default_factory=list)
    macros: List[MacroBlock] = field(default_factory=list)
    human_mode: Optional[str] = None
    comments: List[Comment] = field(default_factory=list)


@dataclass
class SchemaFile(Node):
    """Top-level node for a schema .nodus file."""

    header: Optional[FileHeader] = None
    meta: Optional[Dict[str, Any]] = None
    rules: List[AbsoluteRule] = field(default_factory=list)
    preferences: List[Preference] = field(default_factory=list)
    sections: Dict[str, NamedBlock] = field(default_factory=dict)


@dataclass
class ConfigFile(Node):
    """Top-level node for a config .nodus file."""

    header: Optional[FileHeader] = None
    runtime: Optional[RuntimeBlock] = None
    rules: List[AbsoluteRule] = field(default_factory=list)
    preferences: List[Preference] = field(default_factory=list)
    triggers: List[Trigger] = field(default_factory=list)
    constants: Optional[NamedBlock] = None
    context: Optional[NamedBlock] = None
    error_routing: Optional[NamedBlock] = None
    comments: List[Comment] = field(default_factory=list)


# ─────────────────────────────────────────────
# HEADERS
# ─────────────────────────────────────────────


class FileType(Enum):
    WORKFLOW = "wf"
    SCHEMA = "schema"
    CONFIG = "config"


@dataclass
class FileHeader(Node):
    """§wf:name v1.0 / §schema:nodus v0.3 / §config:project v1.0"""

    file_type: FileType = FileType.WORKFLOW
    name: str = ""
    version: str = ""


# ─────────────────────────────────────────────
# RUNTIME BLOCK
# ─────────────────────────────────────────────


@dataclass
class RuntimeBlock(Node):
    """§runtime: { core: ..., extends: [...], agents: {...}, mode: ... }"""

    core: str = ""
    extends: List[str] = field(default_factory=list)
    agents: Dict[str, str] = field(default_factory=dict)
    mode: str = "production"
    raw_fields: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────
# DECLARATIONS
# ─────────────────────────────────────────────


@dataclass
class Trigger(Node):
    """@ON: condition → action"""

    condition: str = ""
    action: str = ""
    condition_expr: Optional[Node] = None
    action_expr: Optional[Node] = None


@dataclass
class AbsoluteRule(Node):
    """!!NEVER: content / !!ALWAYS: content"""

    rule_type: str = ""  # "NEVER" or "ALWAYS"
    content: str = ""


@dataclass
class Preference(Node):
    """!PREF: a OVER b IF condition"""

    preferred: str = ""
    over: str = ""
    condition: Optional[str] = None


@dataclass
class InputField(Node):
    """Single field in an @in: declaration."""

    name: str = ""
    type_name: str = "any"
    optional: bool = False
    default: Optional[str] = None
    comment: str = ""


@dataclass
class InputDecl(Node):
    """@in: { field: type, ... }"""

    fields: List[InputField] = field(default_factory=list)


@dataclass
class OutputDecl(Node):
    """@out: $variable"""

    variable: str = ""


@dataclass
class ContextDecl(Node):
    """@ctx: [key1, key2, ...]"""

    contexts: List[str] = field(default_factory=list)


@dataclass
class ErrorDecl(Node):
    """@err: ESCALATE(human) +msg=..."""

    handler: Optional[CommandCall] = None
    raw: str = ""


# ─────────────────────────────────────────────
# STEPS
# ─────────────────────────────────────────────


@dataclass
class Step(Node):
    """A numbered step in @steps: block."""

    number: int = 0
    body: Optional[Node] = None
    comment: str = ""
    sub_steps: List[Node] = field(default_factory=list)


# ─────────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────────


@dataclass
class CommandCall(Node):
    """COMMAND(args) +mod=val ^validator ~flag → $target"""

    name: str = ""
    args: List[str] = field(default_factory=list)
    modifiers: Dict[str, str] = field(default_factory=dict)
    validators: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    pipeline_target: Optional[str] = None


# ─────────────────────────────────────────────
# CONTROL FLOW
# ─────────────────────────────────────────────


@dataclass
class Conditional(Node):
    """?IF / ?ELIF / ?ELSE chain."""

    condition: str = ""
    action: Optional[Node] = None
    body: List[Node] = field(default_factory=list)
    break_flag: bool = False
    skip_flag: bool = False
    override_flag: bool = False
    elif_branches: List[Conditional] = field(default_factory=list)
    else_branch: Optional[Conditional] = None


@dataclass
class ForLoop(Node):
    """~FOR $var IN $collection: ... ~END"""

    variable: str = ""
    collection: str = ""
    body: List[Node] = field(default_factory=list)


@dataclass
class UntilLoop(Node):
    """~UNTIL condition | MAX:n: ... ~END"""

    condition: str = ""
    max_iterations: Optional[int] = None
    body: List[Node] = field(default_factory=list)


@dataclass
class ParallelBlock(Node):
    """~PARALLEL: ... ~JOIN → $var"""

    branches: List[Node] = field(default_factory=list)
    join_target: Optional[str] = None


# ─────────────────────────────────────────────
# EXPRESSIONS
# ─────────────────────────────────────────────


@dataclass
class Variable(Node):
    """$name or $name.field.subfield"""

    name: str = ""

    @property
    def parts(self) -> List[str]:
        return self.name.lstrip("$").split(".")


@dataclass
class Literal(Node):
    """A literal value: string, number, bool, null."""

    value: Any = None
    type_name: str = ""  # "str", "int", "float", "bool", "null"


@dataclass
class ArrayLiteral(Node):
    elements: List[Any] = field(default_factory=list)


@dataclass
class ObjectLiteral(Node):
    fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BinaryOp(Node):
    left: Optional[Node] = None
    operator: str = ""
    right: Optional[Node] = None


@dataclass
class Identifier(Node):
    name: str = ""


@dataclass
class WfRef(Node):
    """wf:workflow_name"""

    name: str = ""


@dataclass
class MacroRef(Node):
    """@macro:MACRO_NAME"""

    name: str = ""


# ─────────────────────────────────────────────
# BLOCKS
# ─────────────────────────────────────────────


@dataclass
class NamedBlock(Node):
    """§blockname { ... } — generic named block in schema/config files."""

    name: str = ""
    entries: Dict[str, Any] = field(default_factory=dict)
    raw_lines: List[str] = field(default_factory=list)


@dataclass
class TestBlock(Node):
    """@test:name { input: {}, expected: {}, mock: {}, tags: [] }"""

    name: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    expected: Dict[str, Any] = field(default_factory=dict)
    mock: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    raw_lines: List[str] = field(default_factory=list)


@dataclass
class MacroBlock(Node):
    """@macro:name { ... }"""

    name: str = ""
    body: List[Node] = field(default_factory=list)
    raw_lines: List[str] = field(default_factory=list)


@dataclass
class Comment(Node):
    """A ;; comment line."""

    text: str = ""


# ─────────────────────────────────────────────
# DIAGNOSTIC
# ─────────────────────────────────────────────


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Diagnostic:
    """A lint/parse diagnostic message."""

    severity: Severity
    code: str  # E001, W003, etc.
    message: str
    line: int = 0
    column: int = 0
    filename: str = ""

    def __str__(self) -> str:
        loc = f"{self.filename}:" if self.filename else ""
        return f"{loc}{self.line}:{self.column} [{self.severity.value}] {self.code}: {self.message}"
