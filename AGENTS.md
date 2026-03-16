# Agent Rules

This repository uses the **NODUS Interpretation Protocol** to define how AI agents interact with the system.

For the full technical specification and boot sequence, see:
👉 **[docs/protocol.md](docs/protocol.md)**

## Core Principles for Agents

1. **The Schema is the Authority**: Never improvise beyond the defined keywords in `schema.nodus`.
2. **Strict Adherence**: `!!` (Absolute Rules) are inviolable hard constraints.
3. **Structured Results**: Always return `NODUS:RESULT` after execution.
4. **Boot First**: Load the schema and rules before executing steps.

---
For general documentation, see [docs/README.md](docs/README.md).

## Language Preferences

### Brief overview

This set of guidelines outlines language preferences for the project, ensuring consistency in code and communication.

### Code and documentation language

- All code, comments, documentation, variable names, function names, class names, method names, attribute names, and technical terms must be in English
- Maintain English as the primary language for all technical elements including error messages, log entries, configuration keys, and API responses to ensure readability and maintainability
- Technical documentation, inline comments, docstrings, and README files must be written in English
- All commit messages, pull request descriptions, and issue titles related to code changes should be in English

### Communication style

- Explanations and discussions in the chat interface should be in Russian
- Use Russian for conversational responses, clarifications, project planning, and non-technical interactions
- Project management communications, feature discussions, and strategic decisions should be conducted in Russian
- Code review comments and technical discussions during development can be in Russian unless collaborating with English-speaking developers
