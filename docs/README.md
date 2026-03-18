# NODUS Documentation

Welcome to the Documentation for **NODUS** — a compact, symbolic language for LLM-to-LLM communication.

## Documents

- **[Interpretation Protocol](protocol.md)**  
  The "Boot Sequence" and core identity of a NODUS-compliant agent. Essential reading for implementation.

- **[Syntax & Grammar](syntax.md)**  
  Detailed reference for symbols, operators (`→`, `?IF`), and block structures.

- **[Core Schema Reference](schema.md)**  
  Complete vocabulary of commands (`FETCH`, `GEN`, `VALIDATE`), types, and analytical flags.

- **[CLI & Tooling](cli.md)**  
  User guide for the `nodus` command-line interface and assistant-driven project management.

- **[AI Agent Skill](../.agents/skills/nodus/SKILL.md)**  
  Built-in skill for LLM assistants: guides workflow creation, syntax lookup, lint debugging, and project setup.

## Project Structure

- `packages/spec/core/schema.nodus`: Global vocabulary definitions (downloaded on `nodus init`).
- `packages/spec/core/AGENTS.md`: Agent interpretation protocol.
- `.nodus/config.nodus`: Business logic — global rules, triggers, constants.
- `.nodus/config.json`: Infrastructure — models, API keys, webhooks.
- `workflows/`: Individual `.nodus` files defining specialized tasks.
- `.agents/skills/nodus/`: AI agent skill with syntax cheatsheet, workflow patterns, and lint rules.

---

`NODUS v0.4.0` | "Enough formal to be unambiguous. Enough semantic to preserve intent."
