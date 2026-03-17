"""NODUS Parser — recursive-descent parser for .nodus files.

Consumes tokens produced by the Lexer and builds an AST
using node types from ast_nodes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .lexer import Lexer, Token, TokenType
from .ast_nodes import (
    AbsoluteRule,
    CommandCall,
    Comment,
    Conditional,
    ConfigFile,
    ContextDecl,
    Diagnostic,
    ErrorDecl,
    FileHeader,
    FileType,
    ForLoop,
    InputDecl,
    InputField,
    MacroBlock,
    NamedBlock,
    Node,
    OutputDecl,
    ParallelBlock,
    Position,
    Preference,
    RuntimeBlock,
    SchemaFile,
    Severity,
    Step,
    TestBlock,
    Trigger,
    UntilLoop,
    Variable,
    WorkflowFile,
)


class ParseError(Exception):
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.line = line
        self.column = column
        super().__init__(f"Parse error at {line}:{column}: {message}")


class Parser:
    """Recursive-descent parser for NODUS .nodus files."""

    def __init__(self) -> None:
        self.filename: str = ""
        self.tokens: List[Token] = []
        self.pos: int = 0
        self.diagnostics: List[Diagnostic] = []

    # ═══════════════════════════════════════
    # PUBLIC
    # ═══════════════════════════════════════

    def parse(self, source: str, filename: str = "") -> Optional[Node]:
        """Parse source text into a file-level AST node."""
        self.filename = filename
        self.tokens = Lexer(source, filename).tokenize()
        self.pos = 0
        self.diagnostics = []
        self._skip_noise()
        if self._at_end():
            return None

        tok = self._current()
        if tok.type != TokenType.SECTION:
            self._diag(
                Severity.ERROR, "E000", "Expected § declaration at start of file"
            )
            return None

        val = tok.value
        if val.startswith("\u00a7wf:"):
            return self._parse_workflow()
        if val.startswith("\u00a7schema:"):
            return self._parse_schema()
        if val.startswith("\u00a7config:"):
            return self._parse_config()

        self._diag(Severity.ERROR, "E000", f"Unknown file type: {val}")
        return None

    # ═══════════════════════════════════════
    # WORKFLOW FILE
    # ═══════════════════════════════════════

    def _parse_workflow(self) -> WorkflowFile:
        wf = WorkflowFile(pos=self._pos())
        wf.header = self._parse_header(FileType.WORKFLOW)

        while not self._at_end():
            self._skip_noise()
            if self._at_end():
                break
            tok = self._current()

            if tok.type == TokenType.SECTION:
                if "runtime" in tok.value:
                    wf.runtime = self._parse_runtime()
                else:
                    # sub-workflow declaration or named block — skip
                    self._advance()
                    self._consume_rest_of_line()
            elif tok.type == TokenType.AT_ON:
                wf.triggers.append(self._parse_trigger())
            elif tok.type == TokenType.DOUBLE_BANG:
                wf.rules.append(self._parse_absolute_rule())
            elif tok.type == TokenType.BANG_PREF:
                wf.preferences.append(self._parse_preference())
            elif tok.type == TokenType.AT_IN:
                wf.input_decl = self._parse_input_decl()
            elif tok.type == TokenType.AT_OUT:
                wf.output_decl = self._parse_output_decl()
            elif tok.type == TokenType.AT_CTX:
                wf.context_decl = self._parse_context_decl()
            elif tok.type == TokenType.AT_ERR:
                wf.error_decl = self._parse_error_decl()
            elif tok.type == TokenType.AT_STEPS:
                wf.steps = self._parse_steps()
            elif tok.type == TokenType.AT_TEST:
                wf.tests.append(self._parse_test_block())
            elif tok.type == TokenType.AT_MACRO:
                wf.macros.append(self._parse_macro_block())
            elif tok.type == TokenType.COMMENT:
                text = tok.value
                if "HUMAN MODE" in text:
                    wf.human_mode = self._collect_comment_block()
                else:
                    wf.comments.append(Comment(text=text, pos=self._pos()))
                    self._advance()
            else:
                self._advance()

        return wf

    # ═══════════════════════════════════════
    # SCHEMA FILE
    # ═══════════════════════════════════════

    def _parse_schema(self) -> SchemaFile:
        sf = SchemaFile(pos=self._pos())
        sf.header = self._parse_header(FileType.SCHEMA)

        while not self._at_end():
            self._skip_noise()
            if self._at_end():
                break
            tok = self._current()

            if tok.type == TokenType.DOUBLE_BANG:
                sf.rules.append(self._parse_absolute_rule())
            elif tok.type == TokenType.BANG_PREF:
                sf.preferences.append(self._parse_preference())
            elif tok.type == TokenType.SECTION:
                name = tok.value.replace("\u00a7", "")
                self._advance()
                block = self._parse_named_block(name)
                sf.sections[name] = block
            elif tok.type == TokenType.COMMENT:
                self._advance()
            else:
                self._advance()

        return sf

    # ═══════════════════════════════════════
    # CONFIG FILE
    # ═══════════════════════════════════════

    def _parse_config(self) -> ConfigFile:
        cf = ConfigFile(pos=self._pos())
        cf.header = self._parse_header(FileType.CONFIG)

        while not self._at_end():
            self._skip_noise()
            if self._at_end():
                break
            tok = self._current()

            if tok.type == TokenType.SECTION:
                val = tok.value
                if "runtime" in val:
                    cf.runtime = self._parse_runtime()
                elif "constants" in val:
                    self._advance()
                    cf.constants = self._parse_named_block("constants")
                elif "context" in val:
                    self._advance()
                    cf.context = self._parse_named_block("context")
                elif "error_routing" in val:
                    self._advance()
                    cf.error_routing = self._parse_named_block("error_routing")
                else:
                    self._advance()
                    self._consume_rest_of_line()
            elif tok.type == TokenType.AT_ON:
                cf.triggers.append(self._parse_trigger())
            elif tok.type == TokenType.DOUBLE_BANG:
                cf.rules.append(self._parse_absolute_rule())
            elif tok.type == TokenType.BANG_PREF:
                cf.preferences.append(self._parse_preference())
            elif tok.type == TokenType.COMMENT:
                cf.comments.append(Comment(text=tok.value, pos=self._pos()))
                self._advance()
            else:
                self._advance()

        return cf

    # ═══════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════

    def _parse_header(self, file_type: FileType) -> FileHeader:
        pos = self._pos()
        tok = self._current()
        self._advance()

        # extract name from §type:name
        val = tok.value.replace("\u00a7", "")
        parts = val.split(":", 1)
        name = parts[1] if len(parts) > 1 else parts[0]

        # version
        self._skip_noise()
        version = ""
        if not self._at_end() and self._current().type == TokenType.IDENTIFIER:
            v = self._current().value
            if v.startswith("v"):
                version = v
                self._advance()
                # consume dotted patch segment: v1.0, v0.3.1, etc.
                while not self._at_end() and self._current().type == TokenType.DOT:
                    dot_pos = self.pos
                    self._advance()
                    if not self._at_end() and self._current().type == TokenType.NUMBER:
                        version += "." + self._current().value
                        self._advance()
                    else:
                        self.pos = dot_pos  # backtrack
                        break

        # also accept version split across tokens like "v" NUMBER
        if not version and not self._at_end():
            cur = self._current()
            if cur.type == TokenType.IDENTIFIER and cur.value == "v":
                self._advance()
                if not self._at_end() and self._current().type == TokenType.NUMBER:
                    version = "v" + self._current().value
                    self._advance()

        self._skip_to_newline()
        return FileHeader(file_type=file_type, name=name, version=version, pos=pos)

    # ═══════════════════════════════════════
    # RUNTIME BLOCK
    # ═══════════════════════════════════════

    def _parse_runtime(self) -> RuntimeBlock:
        pos = self._pos()
        self._advance()  # skip §runtime token

        # expect : or {
        self._skip_noise()
        if self._check(TokenType.COLON):
            self._advance()
        self._skip_noise()

        raw: Dict[str, Any] = {}
        if self._check(TokenType.LBRACE):
            raw = self._parse_brace_block()

        rt = RuntimeBlock(pos=pos, raw_fields=raw)
        rt.core = str(raw.get("core", ""))
        rt.mode = str(raw.get("mode", "production"))
        ext = raw.get("extends", [])
        rt.extends = ext if isinstance(ext, list) else [ext]
        agents = raw.get("agents", {})
        rt.agents = agents if isinstance(agents, dict) else {}
        return rt

    # ═══════════════════════════════════════
    # DECLARATIONS
    # ═══════════════════════════════════════

    def _parse_trigger(self) -> Trigger:
        pos = self._pos()
        self._advance()  # skip @ON:
        cond = self._consume_until_arrow()
        action = ""
        if self._check(TokenType.ARROW):
            self._advance()
            action = self._consume_rest_of_line()
        else:
            self._skip_to_newline()
        return Trigger(condition=cond.strip(), action=action.strip(), pos=pos)

    def _parse_absolute_rule(self) -> AbsoluteRule:
        pos = self._pos()
        self._advance()  # skip !!
        rule_type = ""
        if self._check(TokenType.NEVER):
            rule_type = "NEVER"
            self._advance()
        elif self._check(TokenType.ALWAYS):
            rule_type = "ALWAYS"
            self._advance()
        if self._check(TokenType.COLON):
            self._advance()
        content = self._consume_rest_of_line()
        return AbsoluteRule(rule_type=rule_type, content=content.strip(), pos=pos)

    def _parse_preference(self) -> Preference:
        pos = self._pos()
        self._advance()  # skip !PREF:
        line = self._consume_rest_of_line()
        preferred, over, condition = "", "", None
        if " OVER " in line:
            parts = line.split(" OVER ", 1)
            preferred = parts[0].strip()
            rest = parts[1].strip()
            if " IF " in rest:
                over_cond = rest.split(" IF ", 1)
                over = over_cond[0].strip()
                condition = over_cond[1].strip()
            else:
                over = rest
        else:
            preferred = line.strip()
        return Preference(preferred=preferred, over=over, condition=condition, pos=pos)

    def _parse_input_decl(self) -> InputDecl:
        pos = self._pos()
        self._advance()  # skip @in:
        self._skip_noise()
        fields: List[InputField] = []
        if self._check(TokenType.LBRACE):
            self._advance()
            fields = self._parse_field_list()
            if self._check(TokenType.RBRACE):
                self._advance()
        self._skip_to_newline()
        return InputDecl(fields=fields, pos=pos)

    def _parse_field_list(self) -> List[InputField]:
        fields: List[InputField] = []
        while not self._at_end() and not self._check(TokenType.RBRACE):
            self._skip_noise()
            if self._check(TokenType.RBRACE):
                break
            if self._check(TokenType.COMMENT):
                self._advance()
                continue

            if self._check(TokenType.IDENTIFIER) or self._check(TokenType.VARIABLE):
                f = InputField(pos=self._pos())
                f.name = self._current().value
                self._advance()

                # optional ?
                if self._check(TokenType.QUESTION):
                    f.optional = True
                    self._advance()

                # : type
                if self._check(TokenType.COLON):
                    self._advance()
                    self._skip_noise()
                    if not self._at_end() and self._current().type in (
                        TokenType.IDENTIFIER,
                        TokenType.COMMAND_NAME,
                    ):
                        f.type_name = self._current().value
                        self._advance()

                # = default
                if self._check(TokenType.EQUALS):
                    self._advance()
                    self._skip_noise()
                    if not self._at_end() and self._current().type != TokenType.RBRACE:
                        f.default = self._current().value
                        f.optional = True
                        self._advance()

                # inline comment
                if self._check(TokenType.COMMENT):
                    f.comment = self._current().value
                    self._advance()

                fields.append(f)

                if self._check(TokenType.COMMA):
                    self._advance()
            else:
                self._advance()
        return fields

    def _parse_output_decl(self) -> OutputDecl:
        pos = self._pos()
        self._advance()  # skip @out:
        self._skip_noise()
        var = ""
        if self._check(TokenType.VARIABLE):
            var = self._current().value
            self._advance()
        else:
            var = self._consume_rest_of_line().strip()
        self._skip_to_newline()
        return OutputDecl(variable=var, pos=pos)

    def _parse_context_decl(self) -> ContextDecl:
        pos = self._pos()
        self._advance()  # skip @ctx:
        self._skip_noise()
        contexts: List[str] = []
        if self._check(TokenType.LBRACKET):
            self._advance()
            while not self._at_end() and not self._check(TokenType.RBRACKET):
                self._skip_noise()
                if self._check(TokenType.RBRACKET):
                    break
                if self._current().type in (TokenType.IDENTIFIER, TokenType.STRING):
                    contexts.append(self._current().value)
                    self._advance()
                elif self._check(TokenType.COMMA):
                    self._advance()
                else:
                    self._advance()
            if self._check(TokenType.RBRACKET):
                self._advance()
        self._skip_to_newline()
        return ContextDecl(contexts=contexts, pos=pos)

    def _parse_error_decl(self) -> ErrorDecl:
        pos = self._pos()
        self._advance()  # skip @err:
        raw = self._consume_rest_of_line().strip()
        cmd = self._try_parse_command_from_string(raw)
        return ErrorDecl(handler=cmd, raw=raw, pos=pos)

    # ═══════════════════════════════════════
    # STEPS
    # ═══════════════════════════════════════

    def _parse_steps(self) -> List[Step]:
        self._advance()  # skip @steps:
        self._skip_noise()
        steps: List[Step] = []

        while not self._at_end():
            self._skip_noise()
            if self._at_end():
                break
            tok = self._current()

            # stop at non-step constructs
            if tok.type in (
                TokenType.AT_TEST,
                TokenType.AT_MACRO,
                TokenType.SECTION,
                TokenType.EOF,
            ):
                break

            # comment that might be HUMAN MODE
            if tok.type == TokenType.COMMENT:
                if "HUMAN MODE" in tok.value:
                    break
                # step comment — attach to next step
                self._advance()
                continue

            if tok.type == TokenType.STEP_NUMBER:
                steps.append(self._parse_step())
            elif tok.type in (
                TokenType.TILDE_FOR,
                TokenType.TILDE_UNTIL,
                TokenType.TILDE_PARALLEL,
                TokenType.TILDE_END,
                TokenType.TILDE_JOIN,
            ):
                # inline loop/parallel not preceded by step number
                node = self._parse_control_flow()
                if node:
                    steps.append(Step(number=0, body=node, pos=node.pos))
            elif tok.type in (TokenType.Q_IF, TokenType.Q_ELIF, TokenType.Q_ELSE):
                node = self._parse_conditional()
                if node:
                    steps.append(Step(number=0, body=node, pos=node.pos))
            else:
                self._advance()

        return steps

    def _parse_step(self) -> Step:
        pos = self._pos()
        num = int(self._current().value)
        self._advance()  # skip step number
        self._skip_noise()

        step = Step(number=num, pos=pos)

        # comment on step line
        if self._check(TokenType.COMMENT):
            step.comment = self._current().value
            self._advance()
            self._skip_noise()
            return step

        # parse step body
        step.body = self._parse_step_body()

        # collect sub-steps (indented lines that aren't step numbers)
        while not self._at_end():
            self._skip_noise()
            if self._at_end():
                break
            tok = self._current()
            if tok.type == TokenType.STEP_NUMBER:
                break
            if tok.type in (
                TokenType.AT_TEST,
                TokenType.AT_MACRO,
                TokenType.SECTION,
                TokenType.EOF,
            ):
                break
            if tok.type == TokenType.COMMENT:
                if "HUMAN MODE" in tok.value:
                    break
                self._advance()
                continue
            if tok.type == TokenType.TILDE_END:
                self._advance()
                self._skip_to_newline()
                break
            if tok.type in (TokenType.Q_IF, TokenType.Q_ELIF, TokenType.Q_ELSE):
                sub = self._parse_conditional()
                if sub:
                    step.sub_steps.append(sub)
                continue
            if tok.type in (
                TokenType.TILDE_FOR,
                TokenType.TILDE_UNTIL,
                TokenType.TILDE_PARALLEL,
            ):
                sub = self._parse_control_flow()
                if sub:
                    step.sub_steps.append(sub)
                continue
            if tok.type in (TokenType.COMMAND_NAME, TokenType.RUN):
                sub = self._parse_command_call()
                if sub:
                    step.sub_steps.append(sub)
                continue
            # unrecognized indented content
            self._advance()

        return step

    def _parse_step_body(self) -> Optional[Node]:
        if self._at_end():
            return None
        tok = self._current()

        if tok.type in (TokenType.Q_IF, TokenType.Q_ELIF, TokenType.Q_ELSE):
            return self._parse_conditional()
        if tok.type in (
            TokenType.TILDE_FOR,
            TokenType.TILDE_UNTIL,
            TokenType.TILDE_PARALLEL,
        ):
            return self._parse_control_flow()
        if tok.type in (TokenType.COMMAND_NAME, TokenType.RUN):
            return self._parse_command_call()
        if tok.type == TokenType.VARIABLE:
            # assignment: $var = value
            return self._parse_assignment_or_expr()

        # fallback — consume the line
        raw = self._consume_rest_of_line()
        return Comment(text=raw.strip(), pos=self._pos()) if raw.strip() else None

    # ═══════════════════════════════════════
    # COMMAND CALLS
    # ═══════════════════════════════════════

    def _parse_command_call(self) -> CommandCall:
        pos = self._pos()
        name = self._current().value
        self._advance()

        # RUN(@macro:NAME)
        args: List[str] = []
        if self._check(TokenType.LPAREN):
            self._advance()
            args = self._parse_arg_list()
            if self._check(TokenType.RPAREN):
                self._advance()

        mods: Dict[str, str] = {}
        validators: List[str] = []
        flags: List[str] = []
        target: Optional[str] = None

        # collect modifiers, validators, flags, pipeline, and control flags
        while not self._at_end():
            tok = self._current()
            if tok.type == TokenType.MODIFIER:
                mod_name = tok.value
                self._advance()
                mod_val = ""
                if self._check(TokenType.EQUALS):
                    self._advance()
                    mod_val = self._parse_modifier_value()
                mods[mod_name] = mod_val
            elif tok.type == TokenType.VALIDATOR:
                validators.append(tok.value)
                self._advance()
            elif tok.type == TokenType.FLAG:
                flags.append(tok.value)
                self._advance()
            elif tok.type == TokenType.ARROW:
                self._advance()
                self._skip_noise()
                if self._check(TokenType.VARIABLE):
                    target = self._current().value
                    self._advance()
                else:
                    target = self._consume_rest_of_line().strip()
                break
            elif tok.type in (
                TokenType.NEWLINE,
                TokenType.EOF,
                TokenType.COMMENT,
                TokenType.STEP_NUMBER,
                TokenType.Q_IF,
                TokenType.Q_ELIF,
                TokenType.Q_ELSE,
                TokenType.BANG_BREAK,
                TokenType.BANG_SKIP,
                TokenType.BANG_OVERRIDE,
            ):
                break
            else:
                break

        self._skip_to_newline()
        return CommandCall(
            name=name,
            args=args,
            modifiers=mods,
            validators=validators,
            flags=flags,
            pipeline_target=target,
            pos=pos,
        )

    def _parse_arg_list(self) -> List[str]:
        args: List[str] = []
        depth = 0
        current: List[str] = []

        while not self._at_end():
            tok = self._current()
            if tok.type == TokenType.RPAREN and depth == 0:
                break
            if tok.type == TokenType.LPAREN:
                depth += 1
                current.append("(")
                self._advance()
            elif tok.type == TokenType.RPAREN:
                depth -= 1
                current.append(")")
                self._advance()
            elif tok.type == TokenType.COMMA and depth == 0:
                if current:
                    args.append("".join(current).strip())
                    current = []
                self._advance()
            elif tok.type == TokenType.NEWLINE:
                self._advance()
            else:
                current.append(tok.value)
                self._advance()

        if current:
            args.append("".join(current).strip())
        return args

    def _parse_modifier_value(self) -> str:
        """Read a modifier value — could be simple or a brace/bracket block."""
        self._skip_noise()
        if self._at_end():
            return ""

        tok = self._current()
        if tok.type == TokenType.LBRACE:
            return self._collect_brace_raw()
        if tok.type == TokenType.LBRACKET:
            return self._collect_bracket_raw()
        if tok.type in (
            TokenType.VARIABLE,
            TokenType.STRING,
            TokenType.NUMBER,
            TokenType.IDENTIFIER,
            TokenType.TRUE,
            TokenType.FALSE,
            TokenType.NULL,
            TokenType.WF_REF,
            TokenType.COMMAND_NAME,
        ):
            val = tok.value
            self._advance()
            # allow dotted access after identifier
            while self._check(TokenType.DOT):
                self._advance()
                if not self._at_end() and self._current().type in (
                    TokenType.IDENTIFIER,
                    TokenType.COMMAND_NAME,
                ):
                    val += "." + self._current().value
                    self._advance()
            # allow [] index
            if self._check(TokenType.LBRACKET):
                val += self._collect_bracket_raw()
                if self._check(TokenType.DOT):
                    self._advance()
                    if not self._at_end():
                        val += "." + self._current().value
                        self._advance()
            return val
        return ""

    # ═══════════════════════════════════════
    # CONDITIONALS
    # ═══════════════════════════════════════

    def _parse_conditional(self) -> Optional[Conditional]:
        if self._at_end():
            return None
        tok = self._current()

        if tok.type == TokenType.Q_IF:
            return self._parse_if_chain()
        if tok.type == TokenType.Q_ELIF:
            return self._parse_elif()
        if tok.type == TokenType.Q_ELSE:
            return self._parse_else()
        return None

    def _parse_if_chain(self) -> Conditional:
        pos = self._pos()
        self._advance()  # skip ?IF

        cond_str = self._consume_until_action_sep()
        action_node = None
        brk = skip = ovr = False

        # inline form:  ?IF cond → action !BREAK
        # or:  ?IF cond:  (block)
        if self._check(TokenType.ARROW):
            self._advance()
            action_str = self._consume_rest_of_line()
            brk, skip, ovr = self._extract_flags(action_str)
            action_str = self._strip_flags(action_str)
            action_node = self._try_parse_command_from_string(action_str)
        elif self._check(TokenType.COLON):
            self._advance()
            self._skip_to_newline()
        else:
            # bare condition, rest is on same line
            rest = self._consume_rest_of_line()
            brk, skip, ovr = self._extract_flags(rest)

        node = Conditional(
            condition=cond_str.strip(),
            action=action_node,
            break_flag=brk,
            skip_flag=skip,
            override_flag=ovr,
            pos=pos,
        )

        # collect elif / else
        while not self._at_end():
            self._skip_noise()
            if self._at_end():
                break
            if self._check(TokenType.Q_ELIF):
                node.elif_branches.append(self._parse_elif())
            elif self._check(TokenType.Q_ELSE):
                node.else_branch = self._parse_else()
                break
            else:
                break

        return node

    def _parse_elif(self) -> Conditional:
        pos = self._pos()
        self._advance()  # skip ?ELIF
        cond_str = self._consume_until_action_sep()
        action_node = None
        brk = skip = ovr = False

        if self._check(TokenType.ARROW):
            self._advance()
            action_str = self._consume_rest_of_line()
            brk, skip, ovr = self._extract_flags(action_str)
            action_str = self._strip_flags(action_str)
            action_node = self._try_parse_command_from_string(action_str)
        else:
            rest = self._consume_rest_of_line()
            brk, skip, ovr = self._extract_flags(rest)

        return Conditional(
            condition=cond_str.strip(),
            action=action_node,
            break_flag=brk,
            skip_flag=skip,
            override_flag=ovr,
            pos=pos,
        )

    def _parse_else(self) -> Conditional:
        pos = self._pos()
        self._advance()  # skip ?ELSE
        action_node = None
        brk = skip = ovr = False

        if self._check(TokenType.ARROW):
            self._advance()
            action_str = self._consume_rest_of_line()
            brk, skip, ovr = self._extract_flags(action_str)
            action_str = self._strip_flags(action_str)
            action_node = self._try_parse_command_from_string(action_str)
        else:
            rest = self._consume_rest_of_line()
            brk, skip, ovr = self._extract_flags(rest)

        return Conditional(
            condition="",
            action=action_node,
            break_flag=brk,
            skip_flag=skip,
            override_flag=ovr,
            pos=pos,
        )

    # ═══════════════════════════════════════
    # CONTROL FLOW (LOOPS, PARALLEL)
    # ═══════════════════════════════════════

    def _parse_control_flow(self) -> Optional[Node]:
        tok = self._current()
        if tok.type == TokenType.TILDE_FOR:
            return self._parse_for_loop()
        if tok.type == TokenType.TILDE_UNTIL:
            return self._parse_until_loop()
        if tok.type == TokenType.TILDE_PARALLEL:
            return self._parse_parallel()
        if tok.type in (TokenType.TILDE_END, TokenType.TILDE_JOIN):
            self._advance()
            self._skip_to_newline()
            return None
        self._advance()
        return None

    def _parse_for_loop(self) -> ForLoop:
        pos = self._pos()
        self._advance()  # skip ~FOR
        self._skip_noise()

        variable = ""
        if self._check(TokenType.VARIABLE):
            variable = self._current().value
            self._advance()

        # IN
        self._skip_noise()
        if self._check(TokenType.IN):
            self._advance()

        self._skip_noise()
        collection = ""
        if self._check(TokenType.VARIABLE):
            collection = self._current().value
            self._advance()

        if self._check(TokenType.COLON):
            self._advance()
        self._skip_to_newline()

        body = self._collect_body_until_end()
        return ForLoop(variable=variable, collection=collection, body=body, pos=pos)

    def _parse_until_loop(self) -> UntilLoop:
        pos = self._pos()
        self._advance()  # skip ~UNTIL

        # condition | MAX:n:
        cond_parts: List[str] = []
        max_iter: Optional[int] = None

        while not self._at_end():
            tok = self._current()
            if tok.type == TokenType.PIPE:
                self._advance()
                self._skip_noise()
                if self._check(TokenType.MAX):
                    try:
                        max_iter = int(self._current().value)
                    except ValueError:
                        pass
                    self._advance()
                continue
            if tok.type == TokenType.COLON:
                self._advance()
                break
            if tok.type == TokenType.NEWLINE:
                break
            cond_parts.append(tok.value)
            self._advance()

        self._skip_to_newline()
        body = self._collect_body_until_end()
        return UntilLoop(
            condition=" ".join(cond_parts).strip(),
            max_iterations=max_iter,
            body=body,
            pos=pos,
        )

    def _parse_parallel(self) -> ParallelBlock:
        pos = self._pos()
        self._advance()  # skip ~PARALLEL
        if self._check(TokenType.COLON):
            self._advance()
        self._skip_to_newline()

        branches: List[Node] = []
        join_target: Optional[str] = None

        while not self._at_end():
            self._skip_noise()
            if self._at_end():
                break
            tok = self._current()
            if tok.type == TokenType.TILDE_JOIN:
                self._advance()
                if self._check(TokenType.ARROW):
                    self._advance()
                    self._skip_noise()
                    if self._check(TokenType.VARIABLE):
                        join_target = self._current().value
                        self._advance()
                self._skip_to_newline()
                break
            if tok.type == TokenType.TILDE_END:
                self._advance()
                self._skip_to_newline()
                break
            if tok.type in (TokenType.COMMAND_NAME, TokenType.RUN):
                branches.append(self._parse_command_call())
            elif tok.type == TokenType.COMMENT:
                self._advance()
            else:
                self._advance()

        return ParallelBlock(branches=branches, join_target=join_target, pos=pos)

    def _collect_body_until_end(self) -> List[Node]:
        """Collect step body lines until ~END."""
        body: List[Node] = []
        while not self._at_end():
            self._skip_noise()
            if self._at_end():
                break
            tok = self._current()
            if tok.type == TokenType.TILDE_END:
                self._advance()
                self._skip_to_newline()
                break
            if tok.type == TokenType.COMMENT:
                self._advance()
                continue
            node = self._parse_step_body()
            if node:
                body.append(node)
        return body

    # ═══════════════════════════════════════
    # NAMED BLOCKS (schema / config)
    # ═══════════════════════════════════════

    def _parse_named_block(self, name: str) -> NamedBlock:
        pos = self._pos()
        self._skip_noise()

        raw_lines: List[str] = []
        if self._check(TokenType.LBRACE):
            self._advance()
            depth = 1
            while not self._at_end() and depth > 0:
                tok = self._current()
                if tok.type == TokenType.LBRACE:
                    depth += 1
                elif tok.type == TokenType.RBRACE:
                    depth -= 1
                    if depth == 0:
                        self._advance()
                        break
                if tok.type != TokenType.NEWLINE:
                    raw_lines.append(tok.value)
                self._advance()

        self._skip_to_newline()
        return NamedBlock(name=name, raw_lines=raw_lines, pos=pos)

    def _parse_brace_block(self) -> Dict[str, Any]:
        """Parse { key: value, ... } into a dict. Handles nesting."""
        self._advance()  # skip {
        result: Dict[str, Any] = {}

        while not self._at_end() and not self._check(TokenType.RBRACE):
            self._skip_noise()
            if self._check(TokenType.RBRACE):
                break
            if self._check(TokenType.COMMENT):
                self._advance()
                continue

            # key
            if self._current().type in (
                TokenType.IDENTIFIER,
                TokenType.COMMAND_NAME,
                TokenType.STRING,
            ):
                key = self._current().value
                self._advance()

                if self._check(TokenType.COLON):
                    self._advance()
                self._skip_noise()

                # value
                if self._check(TokenType.LBRACE):
                    result[key] = self._parse_brace_block()
                elif self._check(TokenType.LBRACKET):
                    result[key] = self._parse_bracket_list()
                elif not self._at_end() and self._current().type not in (
                    TokenType.RBRACE,
                    TokenType.NEWLINE,
                    TokenType.EOF,
                ):
                    result[key] = self._current().value
                    self._advance()

                if self._check(TokenType.COMMA):
                    self._advance()
            else:
                self._advance()

        if self._check(TokenType.RBRACE):
            self._advance()
        self._skip_to_newline()
        return result

    def _parse_bracket_list(self) -> List[str]:
        """Parse [ val, val, ... ] into a list of strings."""
        self._advance()  # skip [
        items: List[str] = []
        while not self._at_end() and not self._check(TokenType.RBRACKET):
            self._skip_noise()
            if self._check(TokenType.RBRACKET):
                break
            if self._check(TokenType.COMMA):
                self._advance()
                continue
            items.append(self._current().value)
            self._advance()
        if self._check(TokenType.RBRACKET):
            self._advance()
        return items

    # ═══════════════════════════════════════
    # TEST & MACRO BLOCKS
    # ═══════════════════════════════════════

    def _parse_test_block(self) -> TestBlock:
        pos = self._pos()
        name = self._current().value
        self._advance()  # skip @test:name
        self._skip_noise()

        raw_lines: List[str] = []
        if self._check(TokenType.LBRACE):
            self._advance()
            depth = 1
            while not self._at_end() and depth > 0:
                tok = self._current()
                if tok.type == TokenType.LBRACE:
                    depth += 1
                elif tok.type == TokenType.RBRACE:
                    depth -= 1
                    if depth == 0:
                        self._advance()
                        break
                if tok.type != TokenType.NEWLINE:
                    raw_lines.append(tok.value)
                self._advance()

        self._skip_to_newline()
        return TestBlock(name=name, raw_lines=raw_lines, pos=pos)

    def _parse_macro_block(self) -> MacroBlock:
        pos = self._pos()
        name = self._current().value
        self._advance()  # skip @macro:name
        self._skip_noise()

        raw_lines: List[str] = []
        if self._check(TokenType.LBRACE):
            self._advance()
            depth = 1
            while not self._at_end() and depth > 0:
                tok = self._current()
                if tok.type == TokenType.LBRACE:
                    depth += 1
                elif tok.type == TokenType.RBRACE:
                    depth -= 1
                    if depth == 0:
                        self._advance()
                        break
                if tok.type != TokenType.NEWLINE:
                    raw_lines.append(tok.value)
                self._advance()

        self._skip_to_newline()
        return MacroBlock(name=name, raw_lines=raw_lines, pos=pos)

    # ═══════════════════════════════════════
    # ASSIGNMENT
    # ═══════════════════════════════════════

    def _parse_assignment_or_expr(self) -> Optional[Node]:
        """Handle $var = value or standalone variable reference."""
        pos = self._pos()
        var_name = self._current().value
        self._advance()

        if self._check(TokenType.EQUALS):
            self._advance()
            val = self._consume_rest_of_line().strip()
            return CommandCall(
                name="ASSIGN",
                args=[var_name, val],
                pipeline_target=var_name,
                pos=pos,
            )

        self._skip_to_newline()
        return Variable(name=var_name, pos=pos)

    # ═══════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════

    def _pos(self) -> Position:
        if self._at_end():
            return Position(0, 0, self.filename)
        tok = self._current()
        return Position(tok.line, tok.column, self.filename)

    def _at_end(self) -> bool:
        return (
            self.pos >= len(self.tokens) or self.tokens[self.pos].type == TokenType.EOF
        )

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> None:
        if self.pos < len(self.tokens):
            self.pos += 1

    def _check(self, ttype: TokenType) -> bool:
        return not self._at_end() and self._current().type == ttype

    def _skip_noise(self) -> None:
        """Skip NEWLINE tokens."""
        while not self._at_end() and self._current().type == TokenType.NEWLINE:
            self._advance()

    def _skip_to_newline(self) -> None:
        """Advance past the current line."""
        while not self._at_end() and self._current().type != TokenType.NEWLINE:
            self._advance()
        if self._check(TokenType.NEWLINE):
            self._advance()

    def _consume_rest_of_line(self) -> str:
        parts: List[str] = []
        while not self._at_end() and self._current().type not in (
            TokenType.NEWLINE,
            TokenType.EOF,
        ):
            parts.append(self._current().value)
            self._advance()
        if self._check(TokenType.NEWLINE):
            self._advance()
        return " ".join(parts)

    def _consume_until_arrow(self) -> str:
        parts: List[str] = []
        while not self._at_end() and self._current().type not in (
            TokenType.ARROW,
            TokenType.NEWLINE,
            TokenType.EOF,
        ):
            parts.append(self._current().value)
            self._advance()
        return " ".join(parts)

    def _consume_until_action_sep(self) -> str:
        """Consume tokens until →, :, !BREAK, !SKIP, NEWLINE."""
        parts: List[str] = []
        while not self._at_end():
            tok = self._current()
            if tok.type in (
                TokenType.ARROW,
                TokenType.COLON,
                TokenType.NEWLINE,
                TokenType.EOF,
                TokenType.BANG_BREAK,
                TokenType.BANG_SKIP,
                TokenType.BANG_OVERRIDE,
            ):
                break
            parts.append(tok.value)
            self._advance()
        return " ".join(parts)

    def _collect_comment_block(self) -> str:
        """Collect consecutive comment lines into a single string."""
        lines: List[str] = []
        while not self._at_end() and self._current().type == TokenType.COMMENT:
            lines.append(self._current().value)
            self._advance()
            self._skip_noise()
        return "\n".join(lines)

    def _collect_brace_raw(self) -> str:
        """Collect { ... } including nesting as raw string."""
        parts: List[str] = ["{"]
        self._advance()  # skip {
        depth = 1
        while not self._at_end() and depth > 0:
            tok = self._current()
            if tok.type == TokenType.LBRACE:
                depth += 1
            elif tok.type == TokenType.RBRACE:
                depth -= 1
            parts.append(tok.value)
            self._advance()
        return " ".join(parts)

    def _collect_bracket_raw(self) -> str:
        parts: List[str] = ["["]
        self._advance()  # skip [
        depth = 1
        while not self._at_end() and depth > 0:
            tok = self._current()
            if tok.type == TokenType.LBRACKET:
                depth += 1
            elif tok.type == TokenType.RBRACKET:
                depth -= 1
            parts.append(tok.value)
            self._advance()
        return " ".join(parts)

    def _try_parse_command_from_string(self, raw: str) -> Optional[CommandCall]:
        """Best-effort parse of a command string like 'ESCALATE(human) +msg=...'"""
        if not raw:
            return None
        parts = raw.split("(", 1)
        name = parts[0].strip()
        if not name or not name[0].isupper():
            return CommandCall(name=raw, pos=self._pos())
        args: List[str] = []
        if len(parts) > 1:
            arg_str = parts[1].split(")", 1)[0]
            args = [a.strip() for a in arg_str.split(",") if a.strip()]
        return CommandCall(name=name, args=args, pos=self._pos())

    @staticmethod
    def _extract_flags(text: str) -> tuple:
        brk = "!BREAK" in text
        skip = "!SKIP" in text
        ovr = "!OVERRIDE" in text
        return brk, skip, ovr

    @staticmethod
    def _strip_flags(text: str) -> str:
        for flag in ("!BREAK", "!SKIP", "!OVERRIDE"):
            text = text.replace(flag, "")
        return text.strip()

    def _diag(self, severity: Severity, code: str, message: str) -> None:
        pos = self._pos()
        self.diagnostics.append(
            Diagnostic(severity, code, message, pos.line, pos.column, self.filename)
        )
