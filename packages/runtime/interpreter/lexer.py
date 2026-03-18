"""NODUS Lexer — tokenizer for .nodus files.

Converts raw source text into a stream of typed tokens for the parser.
Handles NODUS-specific symbols (§, !!, →, ~, ^, +, $) and all
structural keywords.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from .. import constants

# ═══════════════════════════════════════════════════════════════════════════
# TOKEN TYPES
# ═══════════════════════════════════════════════════════════════════════════


class TokenType(Enum):
    """Enumeration of all valid NODUS token types."""

    # Structure
    SECTION = auto()  # § followed by identifier
    COMMENT = auto()  # ;; ...
    NEWLINE = auto()
    EOF = auto()

    # @ keywords
    AT_ON = auto()  # @ON:
    AT_IN = auto()  # @in:
    AT_OUT = auto()  # @out:
    AT_CTX = auto()  # @ctx:
    AT_ERR = auto()  # @err:
    AT_STEPS = auto()  # @steps:
    AT_TEST = auto()  # @test:name
    AT_MACRO = auto()  # @macro:name

    # ! keywords
    DOUBLE_BANG = auto()  # !!
    BANG_PREF = auto()  # !PREF:
    BANG_BREAK = auto()  # !BREAK
    BANG_SKIP = auto()  # !SKIP
    BANG_OVERRIDE = auto()  # !OVERRIDE

    # ? keywords
    Q_IF = auto()  # ?IF
    Q_ELIF = auto()  # ?ELIF
    Q_ELSE = auto()  # ?ELSE

    # ~ keywords
    TILDE_FOR = auto()  # ~FOR
    TILDE_UNTIL = auto()  # ~UNTIL
    TILDE_PARALLEL = auto()  # ~PARALLEL
    TILDE_JOIN = auto()  # ~JOIN
    TILDE_END = auto()  # ~END
    FLAG = auto()  # ~identifier (analysis flag)

    # Operators
    ARROW = auto()  # →
    PIPE = auto()  # |
    EQUALS = auto()  # =
    NOT_EQUALS = auto()  # !=
    LT = auto()  # <
    GT = auto()  # >
    LTE = auto()  # <=
    GTE = auto()  # >=
    DOUBLE_COLON = auto()  # ::

    # Keywords
    NEVER = auto()
    ALWAYS = auto()
    CONTAINS = auto()
    NOT = auto()
    IN = auto()
    AND = auto()
    OR = auto()
    OVER = auto()
    WITHOUT = auto()
    BEFORE = auto()
    IF = auto()
    MAX = auto()  # MAX:n (value = the number)
    RUN = auto()

    # Literals
    NUMBER = auto()
    STRING = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()

    # Identifiers & references
    VARIABLE = auto()  # $name(.field)*
    MODIFIER = auto()  # +identifier
    VALIDATOR = auto()  # ^identifier(:param)*
    IDENTIFIER = auto()  # generic word
    COMMAND_NAME = auto()  # ALL_CAPS identifier
    WF_REF = auto()  # wf:name
    STEP_NUMBER = auto()  # N. at start of indented context

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COLON = auto()
    COMMA = auto()
    DOT = auto()
    QUESTION = auto()  # ? (optional marker in @in)


# ═══════════════════════════════════════════════════════════════════════════
# TOKEN
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class Token:
    """Represents a single terminal symbol in the NODUS language.

    Attributes:
        type: The category of the token (TokenType).
        value: The raw string value captured from source.
        line: 1-based line number where the token starts.
        column: 1-based column number within the line.
    """

    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        """Formal representation for debugging."""
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


# ═══════════════════════════════════════════════════════════════════════════
# ERRORS
# ═══════════════════════════════════════════════════════════════════════════


class LexerError(Exception):
    """Exception raised when tokenization fails.

    Attributes:
        line: Line number where error occurred.
        column: Column number where error occurred.
        message: Descriptive error message.
    """

    def __init__(self, message: str, line: int, column: int):
        """Initialize with location and message."""
        self.line = line
        self.column = column
        super().__init__(f"Lexer error at {line}:{column}: {message}")


# ═══════════════════════════════════════════════════════════════════════════
# KEYWORD MAPS
# ═══════════════════════════════════════════════════════════════════════════

_KEYWORDS = {
    "NEVER": TokenType.NEVER,
    "ALWAYS": TokenType.ALWAYS,
    "CONTAINS": TokenType.CONTAINS,
    "NOT": TokenType.NOT,
    "IN": TokenType.IN,
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    "OVER": TokenType.OVER,
    "WITHOUT": TokenType.WITHOUT,
    "BEFORE": TokenType.BEFORE,
    "IF": TokenType.IF,
    "RUN": TokenType.RUN,
}

_TILDE_KEYWORDS = {
    "FOR": TokenType.TILDE_FOR,
    "UNTIL": TokenType.TILDE_UNTIL,
    "PARALLEL": TokenType.TILDE_PARALLEL,
    "JOIN": TokenType.TILDE_JOIN,
    "END": TokenType.TILDE_END,
}


# ═══════════════════════════════════════════════════════════════════════════
# LEXER ENGINE
# ═══════════════════════════════════════════════════════════════════════════


class Lexer:
    """Tokenizes a .nodus source string into a stream of Token objects.

    Implements a single-pass scan with lookahead.
    """

    def __init__(self, source: str, filename: str = ""):
        """Initialize the lexer.

        Args:
            source: Raw NODUS code.
            filename: Source file name for diagnostics.
        """
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    # ───────────────────────────────────────────────────────────────────────────
    # Public API
    # ───────────────────────────────────────────────────────────────────────────

    def tokenize(self) -> list[Token]:
        """Convert the entire source string into a list of NODUS tokens.

        Returns:
            A list of Token objects representing the source code.
        """
        while self.pos < len(self.source):
            self._skip_spaces()
            if self._at_end():
                break

            ch = self._ch()

            # Newlines
            if ch in "\r\n":
                self._read_newline()
                continue

            # Comment ;;
            if ch == ";" and self._peek() == ";":
                self._read_comment()
                continue

            # Section §
            if ch == "\u00a7":  # §
                self._read_section()
                continue

            # @ keywords
            if ch == "@":
                self._read_at()
                continue

            # ! keywords or !=
            if ch == "!":
                self._read_bang()
                continue

            # ? keywords
            if ch == "?":
                self._read_question()
                continue

            # ~ keywords / flags
            if ch == "~":
                self._read_tilde()
                continue

            # $ variable
            if ch == "$":
                self._read_variable()
                continue

            # + modifier
            if ch == "+":
                self._read_modifier()
                continue

            # ^ validator
            if ch == "^":
                self._read_validator()
                continue

            # → arrow
            if ch == "\u2192":  # →
                self._emit(TokenType.ARROW, "\u2192")
                self._advance()
                continue

            # Operators
            if ch == "=":
                self._emit(TokenType.EQUALS, "=")
                self._advance()
                continue
            if ch == "<":
                if self._peek() == "=":
                    self._emit(TokenType.LTE, "<=")
                    self._advance()
                    self._advance()
                else:
                    self._emit(TokenType.LT, "<")
                    self._advance()
                continue
            if ch == ">":
                if self._peek() == "=":
                    self._emit(TokenType.GTE, ">=")
                    self._advance()
                    self._advance()
                else:
                    self._emit(TokenType.GT, ">")
                    self._advance()
                continue
            if ch == "|":
                self._emit(TokenType.PIPE, "|")
                self._advance()
                continue

            # Delimiters
            _delim = {
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                ",": TokenType.COMMA,
            }
            if ch in _delim:
                self._emit(_delim[ch], ch)
                self._advance()
                continue

            # String
            if ch == '"':
                self._read_string()
                continue

            # Number (or negative number)
            if ch.isdigit() or (ch == "-" and self._peek_is_digit()):
                self._read_number()
                continue

            # Colon (standalone or ::)
            if ch == ":":
                if self._peek() == ":":
                    self._emit(TokenType.DOUBLE_COLON, "::")
                    self._advance()
                    self._advance()
                else:
                    self._emit(TokenType.COLON, ":")
                    self._advance()
                continue

            # Dot
            if ch == ".":
                self._emit(TokenType.DOT, ".")
                self._advance()
                continue

            # Identifier / keyword / command
            if ch.isalpha() or ch == "_":
                self._read_identifier()
                continue

            # Skip unknown characters
            self._advance()

        self._emit(TokenType.EOF, "")
        return self.tokens

    # ───────────────────────────────────────────────────────────────────────────
    # Character Helpers
    # ───────────────────────────────────────────────────────────────────────────

    def _at_end(self) -> bool:
        """Check if end of source reached."""
        return self.pos >= len(self.source)

    def _ch(self) -> str:
        """Return the character at the current cursor position."""
        return self.source[self.pos]

    def _peek(self) -> str | None:
        """Look at next character without advancing."""
        p = self.pos + 1
        return self.source[p] if p < len(self.source) else None

    def _peek_is_digit(self) -> bool:
        """Check if next character is a digit."""
        p = self.pos + 1
        return p < len(self.source) and self.source[p].isdigit()

    def _advance(self) -> None:
        """Advance cursor and update line/column counters."""
        if self.pos < len(self.source):
            if self.source[self.pos] == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1

    def _emit(self, ttype: TokenType, value: str) -> None:
        """Create and append a new token."""
        self.tokens.append(Token(ttype, value, self.line, self.column))

    def _skip_spaces(self) -> None:
        """Consume all consecutive horizontal whitespace."""
        while self.pos < len(self.source) and self.source[self.pos] in " \t":
            self._advance()

    def _read_word(self) -> str:
        """Accumulate alphanumeric characters into a string."""
        start = self.pos
        while self.pos < len(self.source) and (
            self.source[self.pos].isalnum() or self.source[self.pos] == "_"
        ):
            self.pos += 1
            self.column += 1
        return self.source[start : self.pos]

    # ───────────────────────────────────────────────────────────────────────────
    # Token Readers
    # ───────────────────────────────────────────────────────────────────────────

    def _read_newline(self) -> None:
        """Handle CR/LF and emit a NEWLINE token."""
        self._emit(TokenType.NEWLINE, "\\n")
        if self._ch() == "\r":
            self._advance()
            if not self._at_end() and self._ch() == "\n":
                self._advance()
        else:
            self._advance()

    def _read_comment(self) -> None:
        """Consume double-semicolon comment until EOL."""
        col = self.column
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos] != "\n":
            self.pos += 1
            self.column += 1
        text = self.source[start : self.pos].strip()
        self.tokens.append(Token(TokenType.COMMENT, text, self.line, col))

    def _read_string(self) -> None:
        """Read a double-quoted string with support for escaped quotes."""
        col = self.column
        self._advance()  # skip opening "
        chars: list[str] = []
        while not self._at_end() and self._ch() != '"':
            if self._ch() == "\\" and self._peek() == '"':
                chars.append('"')
                self._advance()
                self._advance()
            else:
                chars.append(self._ch())
                self._advance()
        if not self._at_end():
            self._advance()  # skip closing "
        self.tokens.append(Token(TokenType.STRING, "".join(chars), self.line, col))

    def _read_number(self) -> None:
        """Read an integer or decimal number."""
        col = self.column
        start = self.pos
        if self.source[self.pos] == "-":
            self.pos += 1
            self.column += 1
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self.pos += 1
            self.column += 1

        if self.pos < len(self.source) and self.source[self.pos] == ".":
            after_dot = self.pos + 1
            if after_dot >= len(self.source) or self.source[after_dot] in " \t\n\r":
                num = self.source[start : self.pos]
                self.pos += 1  # skip dot
                self.column += 1
                self.tokens.append(Token(TokenType.STEP_NUMBER, num, self.line, col))
                return
            self.pos += 1
            self.column += 1
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                self.pos += 1
                self.column += 1

        self.tokens.append(
            Token(TokenType.NUMBER, self.source[start : self.pos], self.line, col)
        )

    def _read_section(self) -> None:
        """Read a § section declaration."""
        col = self.column
        self._advance()  # skip §
        word = self._read_word()
        value = "\u00a7" + word  # §word

        if not self._at_end() and self._ch() == ":":
            value += ":"
            self.pos += 1
            self.column += 1
            name = self._read_word()
            value += name

        self.tokens.append(Token(TokenType.SECTION, value, self.line, col))

    def _read_at(self) -> None:
        """Read a @-prefixed keyword or declaration."""
        col = self.column
        self._advance()  # skip @
        word = self._read_word()

        has_colon = not self._at_end() and self._ch() == ":"
        if has_colon:
            self.pos += 1
            self.column += 1

        _at_map = {
            "ON:": TokenType.AT_ON,
            "in:": TokenType.AT_IN,
            "out:": TokenType.AT_OUT,
            "ctx:": TokenType.AT_CTX,
            "err:": TokenType.AT_ERR,
            "steps:": TokenType.AT_STEPS,
        }

        key = word + (":" if has_colon else "")

        if key in _at_map:
            self.tokens.append(Token(_at_map[key], "@" + key, self.line, col))
        elif word == "test" and has_colon:
            name = self._read_word()
            self.tokens.append(Token(TokenType.AT_TEST, name, self.line, col))
        elif word == "macro" and has_colon:
            name = self._read_word()
            self.tokens.append(Token(TokenType.AT_MACRO, name, self.line, col))
        else:
            self.tokens.append(Token(TokenType.IDENTIFIER, "@" + key, self.line, col))

    def _read_bang(self) -> None:
        """Read a !-prefixed rule, flag, or operator."""
        col = self.column
        self._advance()

        if not self._at_end() and self._ch() == "!":
            self._advance()
            self.tokens.append(Token(TokenType.DOUBLE_BANG, "!!", self.line, col))
            return

        if not self._at_end() and self._ch() == "=":
            self._advance()
            self.tokens.append(Token(TokenType.NOT_EQUALS, "!=", self.line, col))
            return

        word = self._read_word()
        has_colon = not self._at_end() and self._ch() == ":"
        if has_colon:
            self.pos += 1
            self.column += 1

        _bang_map = {
            "PREF:": TokenType.BANG_PREF,
            "BREAK": TokenType.BANG_BREAK,
            "SKIP": TokenType.BANG_SKIP,
            "OVERRIDE": TokenType.BANG_OVERRIDE,
        }
        key = word + (":" if has_colon else "")
        if key in _bang_map:
            self.tokens.append(Token(_bang_map[key], "!" + key, self.line, col))
        else:
            self.tokens.append(Token(TokenType.IDENTIFIER, "!" + key, self.line, col))

    def _read_question(self) -> None:
        """Read a ?-prefixed keyword or marker."""
        col = self.column
        self._advance()

        word = self._read_word()
        _q_map = {
            "IF": TokenType.Q_IF,
            "ELIF": TokenType.Q_ELIF,
            "ELSE": TokenType.Q_ELSE,
        }

        if word in _q_map:
            self.tokens.append(Token(_q_map[word], "?" + word, self.line, col))
        else:
            self.tokens.append(Token(TokenType.QUESTION, "?", self.line, col))
            if word:
                self.pos -= len(word)
                self.column -= len(word)

    def _read_tilde(self) -> None:
        """Read a ~-prefixed control flow keyword or flag."""
        col = self.column
        self._advance()
        word = self._read_word()

        if word in _TILDE_KEYWORDS:
            self.tokens.append(Token(_TILDE_KEYWORDS[word], "~" + word, self.line, col))
        else:
            self.tokens.append(Token(TokenType.FLAG, word, self.line, col))

    def _read_variable(self) -> None:
        """Read a $-prefixed variable reference."""
        col = self.column
        self._advance()
        name = self._read_word()

        while not self._at_end() and self._ch() == ".":
            next_pos = self.pos + 1
            if next_pos < len(self.source) and (
                self.source[next_pos].isalpha() or self.source[next_pos] == "_"
            ):
                name += "."
                self.pos += 1
                self.column += 1
                name += self._read_word()
            else:
                break

        self.tokens.append(Token(TokenType.VARIABLE, "$" + name, self.line, col))

    def _read_modifier(self) -> None:
        """Read a +-prefixed modifier."""
        col = self.column
        self._advance()
        name = self._read_word()
        self.tokens.append(Token(TokenType.MODIFIER, "+" + name, self.line, col))

    def _read_validator(self) -> None:
        """Read a ^-prefixed validator."""
        col = self.column
        self._advance()
        name = self._read_word()

        full = name
        while not self._at_end() and self._ch() == ":":
            full += ":"
            self.pos += 1
            self.column += 1
            part: list[str] = []
            while not self._at_end() and self._ch() not in " \t\n\r,)^~+":
                part.append(self._ch())
                self.pos += 1
                self.column += 1
            full += "".join(part)

        self.tokens.append(Token(TokenType.VALIDATOR, "^" + full, self.line, col))

    def _read_identifier(self) -> None:
        """Read generic identifier, keyword, or literal."""
        col = self.column
        word = self._read_word()

        if word == "wf" and not self._at_end() and self._ch() == ":":
            self.pos += 1
            self.column += 1
            name = self._read_word()
            self.tokens.append(Token(TokenType.WF_REF, "wf:" + name, self.line, col))
            return

        if word == "MAX" and not self._at_end() and self._ch() == ":":
            self.pos += 1
            self.column += 1
            num_chars: list[str] = []
            while not self._at_end() and self._ch().isdigit():
                num_chars.append(self._ch())
                self.pos += 1
                self.column += 1
            self.tokens.append(Token(TokenType.MAX, "".join(num_chars), self.line, col))
            return

        if word in _KEYWORDS:
            self.tokens.append(Token(_KEYWORDS[word], word, self.line, col))
            return

        if word == "true":
            self.tokens.append(Token(TokenType.TRUE, word, self.line, col))
            return
        if word == "false":
            self.tokens.append(Token(TokenType.FALSE, word, self.line, col))
            return
        if word == "null":
            self.tokens.append(Token(TokenType.NULL, word, self.line, col))
            return

        if word.isupper() and len(word) > 1 and word in constants.KNOWN_COMMANDS:
            self.tokens.append(Token(TokenType.COMMAND_NAME, word, self.line, col))
            return

        self.tokens.append(Token(TokenType.IDENTIFIER, word, self.line, col))
