"""Tests for the NODUS Lexer."""

from runtime.interpreter.lexer import Lexer, TokenType


def tokenize(source: str):
    return Lexer(source).tokenize()


def types(source: str):
    return [t.type for t in tokenize(source) if t.type != TokenType.EOF]


def values(source: str):
    return [
        t.value
        for t in tokenize(source)
        if t.type not in (TokenType.EOF, TokenType.NEWLINE)
    ]


# ── Section tokens ─────────────────────────────────────────────


def test_section_wf():
    toks = tokenize("§wf:my_workflow")
    assert toks[0].type == TokenType.SECTION
    assert toks[0].value == "§wf:my_workflow"


def test_section_schema():
    toks = tokenize("§schema:nodus")
    assert toks[0].type == TokenType.SECTION
    assert toks[0].value == "§schema:nodus"


def test_section_runtime():
    toks = tokenize("§runtime:")
    assert toks[0].type == TokenType.SECTION


# ── @ keywords ─────────────────────────────────────────────────


def test_at_in():
    toks = [t for t in tokenize("@in:") if t.type != TokenType.NEWLINE]
    assert toks[0].type == TokenType.AT_IN


def test_at_steps():
    toks = [t for t in tokenize("@steps:") if t.type != TokenType.NEWLINE]
    assert toks[0].type == TokenType.AT_STEPS


def test_at_on():
    toks = [t for t in tokenize("@ON:") if t.type != TokenType.NEWLINE]
    assert toks[0].type == TokenType.AT_ON


def test_at_test_with_name():
    toks = tokenize("@test:happy_path")
    at_test = next(t for t in toks if t.type == TokenType.AT_TEST)
    assert at_test.value == "happy_path"


def test_at_macro_with_name():
    toks = tokenize("@macro:QUALITY_LOOP")
    at_macro = next(t for t in toks if t.type == TokenType.AT_MACRO)
    assert at_macro.value == "QUALITY_LOOP"


# ── ! keywords ─────────────────────────────────────────────────


def test_double_bang():
    toks = tokenize("!!NEVER")
    assert toks[0].type == TokenType.DOUBLE_BANG


def test_bang_pref():
    toks = tokenize("!PREF:")
    assert toks[0].type == TokenType.BANG_PREF


def test_bang_break():
    toks = tokenize("!BREAK")
    assert toks[0].type == TokenType.BANG_BREAK


def test_bang_skip():
    toks = tokenize("!SKIP")
    assert toks[0].type == TokenType.BANG_SKIP


def test_not_equals():
    toks = tokenize("!=")
    assert toks[0].type == TokenType.NOT_EQUALS


# ── ? keywords ─────────────────────────────────────────────────


def test_q_if():
    toks = tokenize("?IF")
    assert toks[0].type == TokenType.Q_IF


def test_q_elif():
    toks = tokenize("?ELIF")
    assert toks[0].type == TokenType.Q_ELIF


def test_q_else():
    toks = tokenize("?ELSE")
    assert toks[0].type == TokenType.Q_ELSE


# ── ~ keywords and flags ────────────────────────────────────────


def test_tilde_for():
    toks = tokenize("~FOR")
    assert toks[0].type == TokenType.TILDE_FOR


def test_tilde_until():
    toks = tokenize("~UNTIL")
    assert toks[0].type == TokenType.TILDE_UNTIL


def test_tilde_parallel():
    toks = tokenize("~PARALLEL")
    assert toks[0].type == TokenType.TILDE_PARALLEL


def test_tilde_end():
    toks = tokenize("~END")
    assert toks[0].type == TokenType.TILDE_END


def test_tilde_flag():
    toks = tokenize("~sentiment")
    assert toks[0].type == TokenType.FLAG
    assert toks[0].value == "sentiment"


# ── Variables ───────────────────────────────────────────────────


def test_variable_simple():
    toks = tokenize("$draft")
    assert toks[0].type == TokenType.VARIABLE
    assert toks[0].value == "$draft"


def test_variable_dotted():
    toks = tokenize("$meta.intent")
    assert toks[0].type == TokenType.VARIABLE
    assert toks[0].value == "$meta.intent"


def test_variable_deep():
    toks = tokenize("$in.user.id")
    assert toks[0].type == TokenType.VARIABLE
    assert toks[0].value == "$in.user.id"


# ── Modifiers & validators ──────────────────────────────────────


def test_modifier():
    toks = tokenize("+cache")
    assert toks[0].type == TokenType.MODIFIER
    assert toks[0].value == "+cache"


def test_validator():
    toks = tokenize("^brand_voice")
    assert toks[0].type == TokenType.VALIDATOR
    assert toks[0].value == "^brand_voice"


def test_validator_with_param():
    toks = tokenize("^len:280")
    assert toks[0].type == TokenType.VALIDATOR
    assert toks[0].value == "^len:280"


# ── Operators ───────────────────────────────────────────────────


def test_arrow():
    toks = tokenize("→")
    assert toks[0].type == TokenType.ARROW


def test_lte():
    toks = tokenize("<=")
    assert toks[0].type == TokenType.LTE


def test_gte():
    toks = tokenize(">=")
    assert toks[0].type == TokenType.GTE


def test_lt():
    toks = tokenize("< 0.5")
    assert toks[0].type == TokenType.LT


def test_gt():
    toks = tokenize("> 0.5")
    assert toks[0].type == TokenType.GT


# ── Numbers and step numbers ────────────────────────────────────


def test_integer():
    toks = tokenize("42")
    assert toks[0].type == TokenType.NUMBER
    assert toks[0].value == "42"


def test_float():
    toks = tokenize("0.85")
    assert toks[0].type == TokenType.NUMBER
    assert toks[0].value == "0.85"


def test_negative_number():
    toks = tokenize("-1")
    assert toks[0].type == TokenType.NUMBER
    assert toks[0].value == "-1"


def test_step_number():
    toks = tokenize("1. ")
    assert toks[0].type == TokenType.STEP_NUMBER
    assert toks[0].value == "1"


def test_step_number_multidigit():
    toks = tokenize("12. ")
    assert toks[0].type == TokenType.STEP_NUMBER
    assert toks[0].value == "12"


# ── Strings ─────────────────────────────────────────────────────


def test_string():
    toks = tokenize('"hello world"')
    assert toks[0].type == TokenType.STRING
    assert toks[0].value == "hello world"


def test_string_escaped_quote():
    toks = tokenize(r'"say \"hi\""')
    assert toks[0].type == TokenType.STRING
    assert '"' in toks[0].value


# ── Commands ────────────────────────────────────────────────────


def test_known_command():
    toks = tokenize("FETCH")
    assert toks[0].type == TokenType.COMMAND_NAME


def test_known_command_gen():
    toks = tokenize("GEN")
    assert toks[0].type == TokenType.COMMAND_NAME


def test_unknown_caps_is_identifier():
    # ALL_CAPS but not in _KNOWN_COMMANDS → IDENTIFIER
    toks = tokenize("FOOBAR")
    assert toks[0].type == TokenType.IDENTIFIER


# ── wf: reference ───────────────────────────────────────────────


def test_wf_ref():
    toks = tokenize("wf:some_workflow")
    assert toks[0].type == TokenType.WF_REF
    assert toks[0].value == "wf:some_workflow"


# ── MAX:n ───────────────────────────────────────────────────────


def test_max_token():
    toks = tokenize("MAX:3")
    assert toks[0].type == TokenType.MAX
    assert toks[0].value == "3"


# ── Comments ────────────────────────────────────────────────────


def test_comment():
    toks = tokenize(";; this is a comment")
    assert toks[0].type == TokenType.COMMENT
    assert "this is a comment" in toks[0].value


# ── Booleans & null ─────────────────────────────────────────────


def test_true():
    toks = tokenize("true")
    assert toks[0].type == TokenType.TRUE


def test_false():
    toks = tokenize("false")
    assert toks[0].type == TokenType.FALSE


def test_null():
    toks = tokenize("null")
    assert toks[0].type == TokenType.NULL


# ── Line/column tracking ────────────────────────────────────────


def test_line_tracking():
    toks = tokenize("§wf:foo\n@steps:")
    at_steps = next(t for t in toks if t.type == TokenType.AT_STEPS)
    assert at_steps.line == 2


def test_column_tracking():
    toks = tokenize("§wf:foo")
    assert toks[0].column == 1


# ── Double-colon ────────────────────────────────────────────────


def test_double_colon():
    toks = tokenize("::")
    assert toks[0].type == TokenType.DOUBLE_COLON
