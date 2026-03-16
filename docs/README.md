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

## Project Structure

- `schema.nodus`: Global vocabulary definitions.
- `cli.nodus`: Assistant meta-workflow for managing the project.
- `nodus.config.json`: Project settings and agent bindings.
- `workflows/`: Individual `.nodus` files defining specialized tasks.

---
`NODUS v0.1` | "Enough formal to be unambiguous. Enough semantic to preserve intent."
