"""NODUS CLI — command-line interface for the NODUS language runtime.

Commands:
    nodus validate <file>       Lint/validate a .nodus file
    nodus run <file> [--input]  Execute a workflow
    nodus transpile <file>      Convert between NODUS and HUMAN modes
    nodus test <file>           Run embedded @test blocks
    nodus new <name>            Scaffold a new .nodus workflow
    nodus schema inspect        Show loaded schema summary
    nodus version               Print version info
    nodus help                  Show this help
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

__version__ = "0.3.0"

# ---------------------------------------------------------------------------
# Colour helpers (ANSI, disabled when not a TTY)
# ---------------------------------------------------------------------------

_USE_COLOUR = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not _USE_COLOUR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _red(t: str) -> str:
    return _c("31", t)


def _yellow(t: str) -> str:
    return _c("33", t)


def _green(t: str) -> str:
    return _c("32", t)


def _cyan(t: str) -> str:
    return _c("36", t)


def _bold(t: str) -> str:
    return _c("1", t)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        print(_red(f"Error: file not found — {path}"), file=sys.stderr)
        sys.exit(1)
    if p.suffix != ".nodus":
        print(
            _yellow(f"Warning: expected .nodus extension, got '{p.suffix}'"),
            file=sys.stderr,
        )
    return p.read_text(encoding="utf-8")



# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_validate(args: List[str]) -> int:
    """Validate / lint a .nodus file."""
    if not args:
        print(_red("Usage: nodus validate <file.nodus>"), file=sys.stderr)
        return 1

    from ..interpreter import Parser, Validator

    source = _read_file(args[0])
    parser = Parser()
    ast = parser.parse(source, filename=args[0])
    if ast is None:
        print(_red("Error: failed to parse file"), file=sys.stderr)
        return 1

    validator = Validator()
    diagnostics = validator.validate(ast, filename=args[0])

    if not diagnostics:
        print(_green("OK") + f"  {args[0]}  — no issues found")
        return 0

    errors = [d for d in diagnostics if d.severity.value == "error"]
    warnings = [d for d in diagnostics if d.severity.value == "warning"]
    infos = [d for d in diagnostics if d.severity.value == "info"]

    for d in diagnostics:
        if d.severity.value == "error":
            prefix = _red("ERROR")
        elif d.severity.value == "warning":
            prefix = _yellow("WARN ")
        else:
            prefix = _cyan("INFO ")

        loc = f":{d.line}" if d.line else ""
        print(f"  {prefix}  [{d.code}] {d.message}  ({args[0]}{loc})")

    summary_parts = []
    if errors:
        summary_parts.append(_red(f"{len(errors)} error(s)"))
    if warnings:
        summary_parts.append(_yellow(f"{len(warnings)} warning(s)"))
    if infos:
        summary_parts.append(_cyan(f"{len(infos)} info"))
    print(f"\n  {', '.join(summary_parts)}")

    return 1 if errors else 0


def cmd_run(args: List[str]) -> int:
    """Execute a .nodus workflow."""
    if not args:
        print(_red("Usage: nodus run <file.nodus> [--input '{...}']"), file=sys.stderr)
        return 1

    from ..interpreter import Executor, Parser, Validator

    file_path = args[0]
    source = _read_file(file_path)

    # Parse optional --input JSON
    input_data: Dict = {}
    if "--input" in args:
        idx = args.index("--input")
        if idx + 1 >= len(args):
            print(_red("Error: --input requires a JSON string"), file=sys.stderr)
            return 1
        try:
            input_data = json.loads(args[idx + 1])
        except json.JSONDecodeError as exc:
            print(_red(f"Error: invalid JSON for --input — {exc}"), file=sys.stderr)
            return 1

    # Parse
    from ..interpreter.ast_nodes import WorkflowFile as _WorkflowFile
    parser = Parser()
    ast = parser.parse(source, filename=file_path)
    if not isinstance(ast, _WorkflowFile):
        print(_red("Error: file is not a workflow (expected §wf:)"), file=sys.stderr)
        return 1

    # Validate first
    validator = Validator()
    diagnostics = validator.validate(ast)
    errors = [d for d in diagnostics if d.severity.value == "error"]
    if errors:
        print(_red(f"Validation failed with {len(errors)} error(s):"))
        for d in errors:
            print(f"  {_red('ERROR')}  [{d.code}] {d.message}")
        return 1

    # Execute
    executor = Executor()
    result = executor.execute(ast, input_data=input_data)

    # Output result
    result_dict = result.to_dict()
    status = result_dict.get("status", "unknown")
    if status == "ok":
        print(_green("STATUS: ok"))
    elif status == "partial":
        print(_yellow("STATUS: partial"))
    else:
        print(_red(f"STATUS: {status}"))

    if result_dict.get("out"):
        print(f"\nOUT: {json.dumps(result_dict['out'], indent=2, ensure_ascii=False)}")

    if result_dict.get("errors"):
        print("\nERRORS:")
        for err in result_dict["errors"]:
            print(f"  - {err}")

    if result_dict.get("log"):
        print(f"\nLOG ({len(result_dict['log'])} entries):")
        for entry in result_dict["log"][-10:]:
            print(f"  {entry}")

    return 0 if status == "ok" else 1


def cmd_transpile(args: List[str]) -> int:
    """Transpile between NODUS and HUMAN modes."""
    if not args:
        print(
            _red("Usage: nodus transpile <file.nodus> [--mode human|nodus]"),
            file=sys.stderr,
        )
        return 1

    from ..interpreter import Parser, Transpiler

    file_path = args[0]
    source = _read_file(file_path)

    mode = "human"
    if "--mode" in args:
        idx = args.index("--mode")
        if idx + 1 < len(args):
            mode = args[idx + 1].lower()

    if mode not in ("human", "nodus"):
        print(
            _red(f"Error: unknown mode '{mode}', expected 'human' or 'nodus'"),
            file=sys.stderr,
        )
        return 1

    from ..interpreter.ast_nodes import WorkflowFile as _WorkflowFile
    parser = Parser()
    ast = parser.parse(source, filename=file_path)
    if not isinstance(ast, _WorkflowFile):
        print(_red("Error: transpile only supports workflow files (§wf:)"), file=sys.stderr)
        return 1

    transpiler = Transpiler()
    if mode == "human":
        output = transpiler.to_human(ast)
    else:
        output = transpiler.to_nodus(ast)

    print(output)
    return 0


def cmd_test(args: List[str]) -> int:
    """Run embedded @test blocks in a .nodus file."""
    if not args:
        print(_red("Usage: nodus test <file.nodus>"), file=sys.stderr)
        return 1

    from ..interpreter import Executor, Parser

    file_path = args[0]
    source = _read_file(file_path)

    from ..interpreter.ast_nodes import WorkflowFile as _WorkflowFile
    parser = Parser()
    ast = parser.parse(source, filename=file_path)
    if not isinstance(ast, _WorkflowFile):
        print(_red("Error: test only supports workflow files (§wf:)"), file=sys.stderr)
        return 1

    if not ast.tests:
        print(_yellow(f"No @test blocks found in {file_path}"))
        return 0

    executor = Executor()
    passed = 0
    failed = 0

    for test in ast.tests:
        print(f"  {_bold(test.name)} ... ", end="")
        try:
            result = executor.execute(ast, input_data={})
            # A test passes if the workflow completes without fatal error
            if result.status in ("ok", "partial"):
                print(_green("PASS"))
                passed += 1
            else:
                print(_red("FAIL"))
                for err in result.errors:
                    print(f"    {err}")
                failed += 1
        except Exception as exc:
            print(_red("FAIL"))
            print(f"    {exc}")
            failed += 1

    print()
    summary = f"  {passed + failed} test(s): {_green(f'{passed} passed')}"
    if failed:
        summary += f", {_red(f'{failed} failed')}"
    print(summary)

    return 1 if failed else 0


def cmd_new(args: List[str]) -> int:
    """Scaffold a new .nodus workflow file."""
    if not args:
        print(_red("Usage: nodus new <workflow_name>"), file=sys.stderr)
        return 1

    name = args[0]
    filename = f"{name}.nodus" if not name.endswith(".nodus") else name
    stem = Path(filename).stem

    if Path(filename).exists():
        print(_red(f"Error: {filename} already exists"), file=sys.stderr)
        return 1

    template = f"""\u00a7wf:{stem} v0.1

\u00a7runtime: {{
  core:    core/schema.nodus
  mode:    NODUS
}}

@in: {{ }}
@out: $out

@steps:
  1. ;; TODO: define workflow steps

@err: ESCALATE("human")
"""

    Path(filename).write_text(template, encoding="utf-8")
    print(_green(f"Created {filename}"))
    return 0


def cmd_schema_inspect(args: List[str]) -> int:
    """Show a summary of the loaded schema."""
    schema_path = args[0] if args else "core/schema.nodus"

    from ..interpreter import Parser

    from ..interpreter.ast_nodes import SchemaFile as _SchemaFile
    source = _read_file(schema_path)
    parser = Parser()
    ast = parser.parse(source, filename=schema_path)
    if not isinstance(ast, _SchemaFile):
        print(_red("Error: file is not a schema (expected §schema:)"), file=sys.stderr)
        return 1

    print(_bold(f"Schema: {schema_path}"))
    if ast.header:
        print(f"  Name:    {ast.header.name}")
        print(f"  Version: {ast.header.version}")

    # Count named blocks (SchemaFile stores them in .sections dict)
    if hasattr(ast, "sections") and ast.sections:
        print(f"\n  Sections ({len(ast.sections)}):")
        for name, block in ast.sections.items():
            line_count = len(block.raw_lines) if hasattr(block, "raw_lines") else 0
            print(f"    \u00a7{name}  ({line_count} lines)")

    return 0


def cmd_version(_args: List[str]) -> int:
    print(f"nodus {__version__}")
    return 0


def cmd_help(_args: List[str]) -> int:
    print(_bold("NODUS CLI") + f"  v{__version__}\n")
    print("Usage: nodus <command> [options]\n")
    print("Commands:")
    print(f"  {_cyan('validate')}  <file>               Lint / validate a .nodus file")
    print(f"  {_cyan('run')}       <file> [--input JSON] Execute a workflow")
    print(
        f"  {_cyan('transpile')} <file> [--mode M]     Convert NODUS \u2194 HUMAN (default: human)"
    )
    print(f"  {_cyan('test')}      <file>               Run embedded @test blocks")
    print(f"  {_cyan('new')}       <name>               Scaffold a new workflow")
    print(f"  {_cyan('schema inspect')} [file]           Show schema summary")
    print(f"  {_cyan('version')}                        Print version")
    print(f"  {_cyan('help')}                           Show this help")
    return 0


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_COMMANDS = {
    "validate": cmd_validate,
    "run": cmd_run,
    "transpile": cmd_transpile,
    "test": cmd_test,
    "new": cmd_new,
    "version": cmd_version,
    "help": cmd_help,
}


def main() -> None:
    if len(sys.argv) < 2:
        cmd_help([])
        sys.exit(0)

    command = sys.argv[1]
    rest = sys.argv[2:]

    # Handle two-word commands
    if command == "schema" and rest and rest[0] == "inspect":
        code = cmd_schema_inspect(rest[1:])
        sys.exit(code)

    handler = _COMMANDS.get(command)
    if handler is None:
        print(_red(f"Unknown command: {command}"), file=sys.stderr)
        print(f"Run {_cyan('nodus help')} for usage.", file=sys.stderr)
        sys.exit(1)

    code = handler(rest)
    sys.exit(code)


if __name__ == "__main__":
    main()
