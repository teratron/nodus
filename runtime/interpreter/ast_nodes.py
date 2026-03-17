"""NODUS Abstract Syntax Tree node definitions.

Every parsed .nodus file is represented as a tree of these nodes.
Position information is attached for error reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ─────────────────────────────────────────────
# POSITION
# ─────────────────────────────────────────────


@dataclass
class Position:
    """Source location for error reporting.

    Attributes:
        line: 1-based line number.
        column: 0-based column number.
        filename: Source file path.
    """

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
    """Base class for all AST nodes.

    Attributes:
        pos: Position in the source file.
    """

    pos: Position | None = field(default=None, repr=False)


# ─────────────────────────────────────────────
# FILE-LEVEL NODES
# ─────────────────────────────────────────────


@dataclass
class WorkflowFile(Node):
    """Top-level node for a .nodus workflow file.

    Represents the entire structure of a NODUS workflow including
    headers, rules, inputs, and the step execution sequence.
    """

    header: FileHeader | None = None
    runtime: RuntimeBlock | None = None
    triggers: list[Trigger] = field(default_factory=list)
    rules: list[AbsoluteRule] = field(default_factory=list)
    preferences: list[Preference] = field(default_factory=list)
    input_decl: InputDecl | None = None
    output_decl: OutputDecl | None = None
    context_decl: ContextDecl | None = None
    error_decl: ErrorDecl | None = None
    steps: list[Step] = field(default_factory=list)
    tests: list[NodusTestBlock] = field(default_factory=list)
    macros: list[MacroBlock] = field(default_factory=list)
    human_mode: str | None = None
    comments: list[Comment] = field(default_factory=list)


@dataclass
class SchemaFile(Node):
    """Top-level node for a schema .nodus file.

    Defines the layout, rules, and preferences for a specific NODUS protocol.
    """

    header: FileHeader | None = None
    meta: dict[str, Any] | None = None
    rules: list[AbsoluteRule] = field(default_factory=list)
    preferences: list[Preference] = field(default_factory=list)
    sections: dict[str, NamedBlock] = field(default_factory=dict)


@dataclass
class ConfigFile(Node):
    """Top-level node for a config .nodus file.

    Contains global settings, shared triggers, and environment configuration.
    """

    header: FileHeader | None = None
    runtime: RuntimeBlock | None = None
    rules: list[AbsoluteRule] = field(default_factory=list)
    preferences: list[Preference] = field(default_factory=list)
    triggers: list[Trigger] = field(default_factory=list)
    constants: NamedBlock | None = None
    context: NamedBlock | None = None
    error_routing: NamedBlock | None = None
    comments: list[Comment] = field(default_factory=list)


# ─────────────────────────────────────────────
# HEADERS
# ─────────────────────────────────────────────


class FileType(Enum):
    """Supported NODUS file types."""

    WORKFLOW = "wf"
    SCHEMA = "schema"
    CONFIG = "config"


@dataclass
class FileHeader(Node):
    """File type and version header (e.g., §wf:name v1.0)."""

    file_type: FileType = FileType.WORKFLOW
    name: str = ""
    version: str = ""


# ─────────────────────────────────────────────
# RUNTIME BLOCK
# ─────────────────────────────────────────────


@dataclass
class RuntimeBlock(Node):
    """Runtime configuration block (§runtime).

    Specifies core schema, extensions, and agent metadata.
    """

    core: str = ""
    extends: list[str] = field(default_factory=list)
    agents: dict[str, str] = field(default_factory=dict)
    mode: str = "production"
    raw_fields: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────
# DECLARATIONS
# ─────────────────────────────────────────────


@dataclass
class Trigger(Node):
    """Reactive trigger declaration (@ON)."""

    condition: str = ""
    action: str = ""
    condition_expr: Node | None = None
    action_expr: Node | None = None


@dataclass
class AbsoluteRule(Node):
    """Absolute constraint (!!NEVER or !!ALWAYS)."""

    rule_type: str = ""  # "NEVER" or "ALWAYS"
    content: str = ""


@dataclass
class Preference(Node):
    """Soft preference rule (!PREF)."""

    preferred: str = ""
    over: str = ""
    condition: str | None = None


@dataclass
class InputField(Node):
    """Single field definition in an @in block."""

    name: str = ""
    type_name: str = "any"
    optional: bool = False
    default: str | None = None
    comment: str = ""


@dataclass
class InputDecl(Node):
    """Workflow input declaration (@in)."""

    fields: list[InputField] = field(default_factory=list)


@dataclass
class OutputDecl(Node):
    """Workflow output target declaration (@out)."""

    variable: str = ""


@dataclass
class ContextDecl(Node):
    """Required context keys declaration (@ctx)."""

    contexts: list[str] = field(default_factory=list)


@dataclass
class ErrorDecl(Node):
    """Error handler declaration (@err)."""

    handler: CommandCall | None = None
    raw: str = ""


# ─────────────────────────────────────────────
# STEPS
# ─────────────────────────────────────────────


@dataclass
class Step(Node):
    """A numbered execution step in the @steps block."""

    number: int = 0
    body: Node | None = None
    comment: str = ""
    sub_steps: list[Node] = field(default_factory=list)


# ─────────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────────


@dataclass
class CommandCall(Node):
    """A single command invocation (e.g., FETCH(...))."""

    name: str = ""
    args: list[str] = field(default_factory=list)
    modifiers: dict[str, str] = field(default_factory=dict)
    validators: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    pipeline_target: str | None = None


# ─────────────────────────────────────────────
# CONTROL FLOW
# ─────────────────────────────────────────────


@dataclass
class Conditional(Node):
    """Conditional execution node (?IF / ?ELIF / ?ELSE)."""

    condition: str = ""
    action: Node | None = None
    body: list[Node] = field(default_factory=list)
    break_flag: bool = False
    skip_flag: bool = False
    override_flag: bool = False
    elif_branches: list[Conditional] = field(default_factory=list)
    else_branch: Conditional | None = None


@dataclass
class ForLoop(Node):
    """Iterator loop (~FOR $var IN $collection)."""

    variable: str = ""
    collection: str = ""
    body: list[Node] = field(default_factory=list)


@dataclass
class UntilLoop(Node):
    """Conditional loop (~UNTIL condition | MAX:n)."""

    condition: str = ""
    max_iterations: int | None = None
    body: list[Node] = field(default_factory=list)


@dataclass
class ParallelBlock(Node):
    """Parallel execution block (~PARALLEL ... ~JOIN)."""

    branches: list[Node] = field(default_factory=list)
    join_target: str | None = None


# ─────────────────────────────────────────────
# EXPRESSIONS
# ─────────────────────────────────────────────


@dataclass
class Variable(Node):
    """A NODUS variable expression (e.g., $in.title)."""

    name: str = ""

    @property
    def parts(self) -> list[str]:
        """Split the variable name into segments (dot-notation)."""
        return self.name.lstrip("$").split(".")


@dataclass
class Literal(Node):
    """A literal value node (string, number, boolean, or null)."""

    value: Any = None
    type_name: str = ""  # "str", "int", "float", "bool", "null"


@dataclass
class ArrayLiteral(Node):
    """A literal array of values."""

    elements: list[Any] = field(default_factory=list)


@dataclass
class ObjectLiteral(Node):
    """A literal object (dictionary) of values."""

    fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class BinaryOp(Node):
    """A binary operation (e.g., $val > 5)."""

    left: Node | None = None
    operator: str = ""
    right: Node | None = None


@dataclass
class Identifier(Node):
    """A generic identifier node."""

    name: str = ""


@dataclass
class WfRef(Node):
    """Reference to another workflow (wf:name)."""

    name: str = ""


@dataclass
class MacroRef(Node):
    """Reference to a macro (@macro:name)."""

    name: str = ""


# ─────────────────────────────────────────────
# BLOCKS
# ─────────────────────────────────────────────


@dataclass
class NamedBlock(Node):
    """Generic named block in schema or config files (§name)."""

    name: str = ""
    entries: dict[str, Any] = field(default_factory=dict)
    raw_lines: list[str] = field(default_factory=list)


@dataclass
class NodusTestBlock(Node):
    """Simulation test definition (@test)."""

    __test__ = False

    name: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    expected: dict[str, Any] = field(default_factory=dict)
    mock: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)


@dataclass
class MacroBlock(Node):
    """Reusable macro definition (@macro)."""

    name: str = ""
    body: list[Node] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)


@dataclass
class Comment(Node):
    """A NODUS comment line (;;)."""

    text: str = ""


# ─────────────────────────────────────────────
# DIAGNOSTIC
# ─────────────────────────────────────────────


class Severity(Enum):
    """Diagnostic severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Diagnostic:
    """A lint or parse diagnostic message."""

    severity: Severity
    code: str  # E001, W003, etc.
    message: str
    line: int = 0
    column: int = 0
    filename: str = ""

    def __str__(self) -> str:
        loc = f"{self.filename}:" if self.filename else ""
        return f"{loc}{self.line}:{self.column} [{self.severity.value}] {self.code}: {self.message}"
