# Structure

## Magic Spec Structure with Nodus

[Magic Spec](https://github.com/teratron/magic-spec)

```
magic-spec/
│
├── .agents/                   ← AI-интерфейс (единая точка входа для ИИ)
│   ├── rules/                 ← правила генерации (markdown.md и т.д.)
│   ├── skills/
│   │   └── nodus/             ← NODUS skill для AI-ассистентов
│   │       ├── SKILL.md
│   │       └── references/
│   └── workflows/             ← slash-команды
│       ├── magic.*.md         ← команды Magic Spec
│       └── nodus.*.md         ← команды NODUS
│
├── .magic/                    ← движок Magic Spec (не редактировать)
│
├── .nodus/                    ← NODUS infrastructure (не редактировать)
│   ├── core/
│   ├── schema/
│   └── config.json
│
├── .design/                   ← SDD-артефакты Magic Spec
│   ├── INDEX.md
│   ├── RULES.md
│   └── specifications/
│
├── packages/                  ← код продукта
│   ├── spec/
│   ├── runtime/
│   └── extensions/
│
├── workflows/                 ← NODUS-воркфлоу для автоматизации Magic Spec
│   └── internal/
│       ├── publish.nodus
│       └── version_bump.nodus
│
└── docs/
```

## User Project Structure with Magic Spec

```
my-project/
│
├── .agents/                       ← AI-интерфейс
│   ├── rules/
│   ├── skills/
│   │   ├── nodus/                 ← устанавливает nodus init
│   │   └── project-specific/      ← пользователь добавляет свои
│   └── workflows/
│       ├── magic.*.md             ← устанавливает magic init
│       └── nodus.*.md             ← устанавливает nodus init
│
├── .magic/                        ← Magic Spec engine (nodus init не трогает)
│
├── .nodus/                        ← all NODUS infrastructure (created by nodus init)
│   ├── core/                      ← language core (don't edit)
│   │   ├── schema.nodus
│   │   ├── AGENTS.md
│   │   └── cli.nodus
│   ├── extensions/                ← installed packs (nodus install, don't edit)
│   │   └── nodus-social@1.0/
│   ├── schema/                    ← user schema extensions
│   │   ├── brand_voice.nodus
│   │   └── validators.nodus
│   ├── context/                   ← static context files loaded via @ctx
│   │   ├── brand_voice.md
│   │   └── tone_guidelines.md
│   ├── config.json                ← infrastructure: models, API keys, webhooks
│   └── .cache/                    ← generated at runtime (gitignore)
│       └── nodus.lock
│
├── .design/                       ← SDD-артефакты проекта сгенерированные Magic Spec
│   ├── INDEX.md
│   ├── RULES.md
│   └── specifications/
│
├── workflows/                     ← user workflows (name and location is flexible)
│   ├── _shared/                   ← reusable sub-workflows
│   ├── social/
│   └── support/
│
├── src/                           ← код проекта (обычная структура)
│
├── config.nodus                   ← business logic: rules, triggers, constants
├── logs/                          ← execution logs (NODUS:RESULT objects)
└── tests/                         ← workflow test cases (.test.json)
```
