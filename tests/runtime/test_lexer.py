"""Tests for the NODUS Lexer.

Verifies tokenization logic for all keywords, symbols, variables, and tracking.
"""

from __future__ import annotations

from typing import Any

from runtime.interpreter.lexer import Lexer, Token, TokenType


def tokenize(source: str) -> list[Token]:
    """Tokenize source string.

    Args:
        source: Input code string.

    Returns:
        List of Token objects.
    """
    return Lexer(source).tokenize()


def types(source: str) -> list[TokenType]:
    """Extract token types from source.

    Args:
        source: Input code string.

    Returns:
        List of TokenType enums.
    """
    return [t.type for t in tokenize(source) if t.type != TokenType.EOF]


def values(source: str) -> list[Any]:
    """Extract token values from source.

    Args:
        source: Input code string.

    Returns:
        List of token value strings.
    """
    return [
        t.value
        for t in tokenize(source)
        if t.type not in (TokenType.EOF, TokenType.NEWLINE)
    ]


# ───────────────────────────────────────────────────────────────────────────
# Section tokens
# ───────────────────────────────────────────────────────────────────────────


def test_section_wf() -> None:
    """Verify Lexer correctly identifies workflow section tokens."""
    toks = tokenize("\u00a7wf:my_workflow")
    assert toks[0].type == TokenType.SECTION
    assert toks[0].value == "\u00a7wf:my_workflow"


def test_section_schema() -> None:
    """Verify Lexer correctly identifies schema section tokens."""
    toks = tokenize("\u00a7schema:nodus")
    assert toks[0].type == TokenType.SECTION
    assert toks[0].value == "\u00a7schema:nodus"


def test_section_runtime() -> None:
    """Verify Lexer correctly identifies runtime section tokens."""
    toks = tokenize("\u00a7runtime:")
    assert toks[0].type == TokenType.SECTION


# ───────────────────────────────────────────────────────────────────────────
# @ keywords
# ───────────────────────────────────────────────────────────────────────────


def test_at_in() -> None:
    """Verify Lexer handles @in: keyword."""
    toks = [t for t in tokenize("@in:") if t.type != TokenType.NEWLINE]
    assert toks[0].type == TokenType.AT_IN


def test_at_steps() -> None:
    """Verify Lexer handles @steps: keyword."""
    toks = [t for t in tokenize("@steps:") if t.type != TokenType.NEWLINE]
    assert toks[0].type == TokenType.AT_STEPS


def test_at_on() -> None:
    """Verify Lexer handles @ON: keyword."""
    toks = [t for t in tokenize("@ON:") if t.type != TokenType.NEWLINE]
    assert toks[0].type == TokenType.AT_ON


def test_at_test_with_name() -> None:
    """Verify Lexer handles @test:name keyword."""
    toks = tokenize("@test:happy_path")
    at_test = next(t for t in toks if t.type == TokenType.AT_TEST)
    assert at_test.value == "happy_path"


def test_at_macro_with_name() -> None:
    """Verify Lexer handles @macro:name keyword."""
    toks = tokenize("@macro:QUALITY_LOOP")
    at_macro = next(t for t in toks if t.type == TokenType.AT_MACRO)
    assert at_macro.value == "QUALITY_LOOP"


# ───────────────────────────────────────────────────────────────────────────
# ! keywords
# ───────────────────────────────────────────────────────────────────────────


def test_double_bang() -> None:
    """Verify Lexer handles !! double bang."""
    toks = tokenize("!!NEVER")
    assert toks[0].type == TokenType.DOUBLE_BANG


def test_bang_pref() -> None:
    """Verify Lexer handles !PREF: keyword."""
    toks = tokenize("!PREF:")
    assert toks[0].type == TokenType.BANG_PREF


def test_bang_break() -> None:
    """Verify Lexer handles !BREAK control flag."""
    toks = tokenize("!BREAK")
    assert toks[0].type == TokenType.BANG_BREAK


def test_bang_skip() -> None:
    """Verify Lexer handles !SKIP control flag."""
    toks = tokenize("!SKIP")
    assert toks[0].type == TokenType.BANG_SKIP


def test_not_equals() -> None:
    """Verify Lexer handles != operator."""
    toks = tokenize("!=")
    assert toks[0].type == TokenType.NOT_EQUALS


# ───────────────────────────────────────────────────────────────────────────
# ? keywords
# ───────────────────────────────────────────────────────────────────────────


def test_q_if() -> None:
    """Verify Lexer handles ?IF conditional keyword."""
    toks = tokenize("?IF")
    assert toks[0].type == TokenType.Q_IF


def test_q_elif() -> None:
    """Verify Lexer handles ?ELIF conditional keyword."""
    toks = tokenize("?ELIF")
    assert toks[0].type == TokenType.Q_ELIF


def test_q_else() -> None:
    """Verify Lexer handles ?ELSE conditional keyword."""
    toks = tokenize("?ELSE")
    assert toks[0].type == TokenType.Q_ELSE


# ───────────────────────────────────────────────────────────────────────────
# ~ keywords and flags
# ───────────────────────────────────────────────────────────────────────────


def test_tilde_for() -> None:
    """Verify Lexer handles ~FOR loop keyword."""
    toks = tokenize("~FOR")
    assert toks[0].type == TokenType.TILDE_FOR


def test_tilde_until() -> None:
    """Verify Lexer handles ~UNTIL loop keyword."""
    toks = tokenize("~UNTIL")
    assert toks[0].type == TokenType.TILDE_UNTIL


def test_tilde_parallel() -> None:
    """Verify Lexer handles ~PARALLEL block keyword."""
    toks = tokenize("~PARALLEL")
    assert toks[0].type == TokenType.TILDE_PARALLEL


def test_tilde_end() -> None:
    """Verify Lexer handles ~END block closer."""
    toks = tokenize("~END")
    assert toks[0].type == TokenType.TILDE_END


def test_tilde_flag() -> None:
    """Verify Lexer handles ~flag identifier."""
    toks = tokenize("~sentiment")
    assert toks[0].type == TokenType.FLAG
    assert toks[0].value == "sentiment"


# ───────────────────────────────────────────────────────────────────────────
# Variables
# ───────────────────────────────────────────────────────────────────────────


def test_variable_simple() -> None:
    """Verify Lexer handles simple $vars."""
    toks = tokenize("$draft")
    assert toks[0].type == TokenType.VARIABLE
    assert toks[0].value == "$draft"


def test_variable_dotted() -> None:
    """Verify Lexer handles dotted $vars."""
    toks = tokenize("$meta.intent")
    assert toks[0].type == TokenType.VARIABLE
    assert toks[0].value == "$meta.intent"


def test_variable_deep() -> None:
    """Verify Lexer handles multi-level dotted $vars."""
    toks = tokenize("$in.user.id")
    assert toks[0].type == TokenType.VARIABLE
    assert toks[0].value == "$in.user.id"


# ───────────────────────────────────────────────────────────────────────────
# Modifiers & validators
# ───────────────────────────────────────────────────────────────────────────


def test_modifier() -> None:
    """Verify Lexer handles +modifier keywords."""
    toks = tokenize("+cache")
    assert toks[0].type == TokenType.MODIFIER
    assert toks[0].value == "+cache"


def test_validator() -> None:
    """Verify Lexer handles ^validator keywords."""
    toks = tokenize("^brand_voice")
    assert toks[0].type == TokenType.VALIDATOR
    assert toks[0].value == "^brand_voice"


def test_validator_with_param() -> None:
    """Verify Lexer handles parameterized ^validators."""
    toks = tokenize("^len:280")
    assert toks[0].type == TokenType.VALIDATOR
    assert toks[0].value == "^len:280"


# ───────────────────────────────────────────────────────────────────────────
# Operators
# ───────────────────────────────────────────────────────────────────────────


def test_arrow() -> None:
    """Verify Lexer handles \u2192 arrow operator."""
    toks = tokenize("\u2192")
    assert toks[0].type == TokenType.ARROW


def test_lte() -> None:
    """Verify Lexer handles <= operator."""
    toks = tokenize("<=")
    assert toks[0].type == TokenType.LTE


def test_gte() -> None:
    """Verify Lexer handles >= operator."""
    toks = tokenize(">=")
    assert toks[0].type == TokenType.GTE


def test_lt() -> None:
    """Verify Lexer handles < operator."""
    toks = tokenize("< 0.5")
    assert toks[0].type == TokenType.LT


def test_gt() -> None:
    """Verify Lexer handles > operator."""
    toks = tokenize("> 0.5")
    assert toks[0].type == TokenType.GT


# ───────────────────────────────────────────────────────────────────────────
# Numbers and step numbers
# ───────────────────────────────────────────────────────────────────────────


def test_integer() -> None:
    """Verify Lexer handles integer literals."""
    toks = tokenize("42")
    assert toks[0].type == TokenType.NUMBER
    assert toks[0].value == "42"


def test_float() -> None:
    """Verify Lexer handles float literals."""
    toks = tokenize("0.85")
    assert toks[0].type == TokenType.NUMBER
    assert toks[0].value == "0.85"


def test_negative_number() -> None:
    """Verify Lexer handles negative numbers."""
    toks = tokenize("-1")
    assert toks[0].type == TokenType.NUMBER
    assert toks[0].value == "-1"


def test_step_number() -> None:
    """Verify Lexer handles step number prefixes (1. )."""
    toks = tokenize("1. ")
    assert toks[0].type == TokenType.STEP_NUMBER
    assert toks[0].value == "1"


def test_step_number_multidigit() -> None:
    """Verify Lexer handles multi-digit step numbers."""
    toks = tokenize("12. ")
    assert toks[0].type == TokenType.STEP_NUMBER
    assert toks[0].value == "12"


# ───────────────────────────────────────────────────────────────────────────
# Strings
# ───────────────────────────────────────────────────────────────────────────


def test_string() -> None:
    """Verify Lexer handles double-quoted strings."""
    toks = tokenize('"hello world"')
    assert toks[0].type == TokenType.STRING
    assert toks[0].value == "hello world"


def test_string_escaped_quote() -> None:
    """Verify Lexer handles escaped quotes in strings."""
    toks = tokenize(r'"say \"hi\""')
    assert toks[0].type == TokenType.STRING
    assert '"' in toks[0].value


# ───────────────────────────────────────────────────────────────────────────
# Commands
# ───────────────────────────────────────────────────────────────────────────


def test_known_command() -> None:
    """Verify Lexer recognizes built-in FETCH command."""
    toks = tokenize("FETCH")
    assert toks[0].type == TokenType.COMMAND_NAME


def test_known_command_gen() -> None:
    """Verify Lexer recognizes built-in GEN command."""
    toks = tokenize("GEN")
    assert toks[0].type == TokenType.COMMAND_NAME


def test_unknown_caps_is_identifier() -> None:
    """Verify unknown ALL_CAPS strings are treated as identifiers."""
    toks = tokenize("FOOBAR")
    assert toks[0].type == TokenType.IDENTIFIER


# ───────────────────────────────────────────────────────────────────────────
# wf: reference
# ───────────────────────────────────────────────────────────────────────────


def test_wf_ref() -> None:
    """Verify Lexer handles wf: references."""
    toks = tokenize("wf:some_workflow")
    assert toks[0].type == TokenType.WF_REF
    assert toks[0].value == "wf:some_workflow"


# ───────────────────────────────────────────────────────────────────────────
# MAX:n
# ───────────────────────────────────────────────────────────────────────────


def test_max_token() -> None:
    """Verify Lexer handles MAX:n tokens for until-loops."""
    toks = tokenize("MAX:3")
    assert toks[0].type == TokenType.MAX
    assert toks[0].value == "3"


# ───────────────────────────────────────────────────────────────────────────
# Comments
# ───────────────────────────────────────────────────────────────────────────


def test_comment() -> None:
    """Verify Lexer handles ;; comments."""
    toks = tokenize(";; this is a comment")
    assert toks[0].type == TokenType.COMMENT
    assert "this is a comment" in toks[0].value


# ───────────────────────────────────────────────────────────────────────────
# Booleans & null
# ───────────────────────────────────────────────────────────────────────────


def test_true() -> None:
    """Verify Lexer handles true literal."""
    toks = tokenize("true")
    assert toks[0].type == TokenType.TRUE


def test_false() -> None:
    """Verify Lexer handles false literal."""
    toks = tokenize("false")
    assert toks[0].type == TokenType.FALSE


def test_null() -> None:
    """Verify Lexer handles null literal."""
    toks = tokenize("null")
    assert toks[0].type == TokenType.NULL


# ───────────────────────────────────────────────────────────────────────────
# Line/column tracking
# ───────────────────────────────────────────────────────────────────────────


def test_line_tracking() -> None:
    """Verify Lexer correctly tracks line numbers."""
    toks = tokenize("\u00a7wf:foo\n@steps:")
    at_steps = next(t for t in toks if t.type == TokenType.AT_STEPS)
    assert at_steps.line == 2


def test_column_tracking() -> None:
    """Verify Lexer correctly tracks column positions."""
    toks = tokenize("\u00a7wf:foo")
    assert toks[0].column == 1


# ───────────────────────────────────────────────────────────────────────────
# Double-colon
# ───────────────────────────────────────────────────────────────────────────


def test_double_colon() -> None:
    """Verify Lexer handles double-colon tokens."""
    toks = tokenize("::")
    assert toks[0].type == TokenType.DOUBLE_COLON
