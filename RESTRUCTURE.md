# NODUS — План реструктуризации проекта

## Целевая структура

```
nodus/                                 ← github.com/nodus-lang/nodus
│
├── packages/
│   │
│   ├── spec/                          ← СПЕЦИФИКАЦИЯ ЯЗЫКА (меняется медленно)
│   │   ├── core/
│   │   │   ├── schema.nodus           ← словарь языка
│   │   │   ├── schema.types.nodus
│   │   │   ├── schema.errors.nodus
│   │   │   ├── grammar.peg            ← формальная грамматика
│   │   │   └── AGENTS.md             ← протокол для агентов
│   │   ├── templates/
│   │   │   ├── workflow.template.nodus
│   │   │   └── schema.template.nodus
│   │   └── VERSION                    ← версия спецификации отдельно
│   │
│   ├── runtime/                       ← PYTHON RUNTIME (меняется часто)
│   │   ├── interpreter/
│   │   │   ├── lexer.py
│   │   │   ├── parser.py
│   │   │   ├── ast_nodes.py
│   │   │   ├── validator.py
│   │   │   ├── executor.py
│   │   │   └── transpiler.py
│   │   ├── cli/
│   │   │   └── nodus.py
│   │   ├── constants.py
│   │   ├── settings.py
│   │   └── __init__.py
│   │
│   └── extensions/                    ← IDE support
│       ├── vscode/                    ← VS CODE EXTENSION (своя экосистема)
│       │   ├── src/
│       │   ├── package.json
│       │   └── README.md
│       └── jetbrains/                 ← JetBrains IDEs (planned)
│           ├── README.md
│           └── ...
│
├── packs/                             ← ОФИЦИАЛЬНЫЕ ПАКИ (независимый цикл)
│   └── nodus-social/
│       ├── pack.json
│       ├── schema.nodus
│       └── workflows/
│
├── examples/                          ← КАНОНИЧЕСКИЕ ПРИМЕРЫ ЯЗЫКА
│   │                                    (минималистичные, для обучения)
│   ├── social/
│   │   └── beautiful_mention.nodus    ← ~10 строк, только суть
│   └── support/
│       └── ticket_triage.nodus
│
├── demo/                              ← ЖИВОЙ ДЕМО-ПРОЕКТ
│   │                                    (показывает реальный проект пользователя)
│   ├── .nodus/
│   │   ├── core/                      ← symlink → packages/spec/core/
│   │   ├── schema/
│   │   │   ├── brand_voice.nodus
│   │   │   └── validators.nodus
│   │   └── config.json
│   ├── config.nodus                   ← вот где ему место
│   ├── workflows/
│   │   └── beautiful_mention.nodus    ← полный production-ready вариант
│   └── context/
│       ├── brand_voice.md
│       └── tone_guidelines.md
│
├── docs/                              ← ДОКУМЕНТАЦИЯ
│   ├── syntax.md
│   ├── schema.md
│   ├── protocol.md
│   ├── cli.md
│   └── README.md
│
├── tests/                             ← ТЕСТЫ RUNTIME
│   └── runtime/
│       ├── test_lexer.py
│       ├── test_parser.py
│       ├── test_validator.py
│       ├── test_executor.py
│       └── test_transpiler.py
│
├── pyproject.toml
├── AGENTS.md                          ← правила для разработчиков проекта
├── README.md
├── CONTRIBUTING.md
└── CHANGELOG.md
```

---

## Что куда переехало и почему

| Сейчас | После | Причина |
| --- | --- | --- |
| `core/` | `packages/spec/core/` | spec — отдельная сущность от runtime |
| `runtime/` | `packages/runtime/` | явная граница пакета |
| `vscode-extension/` | `packages/extensions/vscode/` | своя npm-экосистема |
| `config.nodus` (корень) | `demo/config.nodus` | принадлежит проекту, не языку |
| `context/` (корень) | `demo/context/` | то же самое |
| `workflows/` (корень) | `demo/workflows/` | демо-проект, не часть языка |
| `examples/social/beautiful_mention.nodus` | `examples/social/` | остаётся, это обучающий пример |
| `workflows/beautiful_mention.nodus` | `demo/workflows/` | это production-пример |
| `templates/` | `packages/spec/templates/` | часть спецификации |

---

## Решение проблемы дубля beautiful_mention

Два файла остаются, но с чёткими ролями:

**`examples/social/beautiful_mention.nodus`** — обучающий пример.
Минималистичный (~10-15 строк), показывает синтаксис.
Аудитория: человек, который впервые читает документацию.

**`demo/workflows/beautiful_mention.nodus`** — production-пример.
Полный (300+ строк), показывает реальный проект.
Аудитория: разработчик, который внедряет NODUS в свой продукт.

Это разные документы с разными задачами. Дубль — не проблема, проблема была в отсутствии контекста.

---

## Граница spec ↔ runtime

Это самое важное архитектурное правило:

```
packages/spec/     →  НЕ импортирует ничего из packages/runtime/
packages/runtime/  →  читает файлы из packages/spec/ как данные (не как код)
```

Спецификация — это текстовые файлы (.nodus, .peg, .md).
Runtime — это код, который их интерпретирует.
Они не должны знать друг о друге на уровне кода.

---

## Plan миграции — пошагово

### Шаг 1 — Создать скелет новой структуры

```bash
mkdir -p packages/spec/core
mkdir -p packages/spec/templates
mkdir -p packages/runtime
mkdir -p packages/extensions/vscode
mkdir -p demo/.nodus/core
mkdir -p demo/.nodus/schema
mkdir -p demo/workflows
mkdir -p demo/context
```

### Шаг 2 — Переместить spec

```bash
mv core/                    packages/spec/core/
mv templates/               packages/spec/templates/
```

### Шаг 3 — Переместить runtime

```bash
mv runtime/                 packages/runtime/
mv pyproject.toml           packages/runtime/pyproject.toml
mv tests/                   packages/runtime/tests/
```

Обновить `pyproject.toml`: пути к пакетам изменились.

### Шаг 4 — Переместить demo-проект

```bash
mv config.nodus             demo/config.nodus
mv context/                 demo/context/
mv workflows/               demo/workflows/
mv .nodus/                  demo/.nodus/
```

Обновить все пути внутри `config.nodus` и `demo/.nodus/config.json`.

### Шаг 5 — Переместить VS Code extension

```bash
mv vscode-extension/        packages/vscode/
```

### Шаг 6 — Обновить корневой pyproject.toml

```toml
[tool.hatch.build.targets.wheel]
packages = ["packages/runtime/runtime"]
```

### Шаг 7 — Обновить пути в settings.py

```python
DEFAULT_SCHEMA_PATH = "packages/spec/core/schema.nodus"
```

### Шаг 8 — Обновить CONTRIBUTING.md и README.md

Отразить новую структуру.

### Шаг 9 — Версия

```
pyproject.toml:    0.3.8 → 0.3.9
constants.py:      0.3.8 → 0.3.9
CHANGELOG.md:      добавить [0.3.9] - Restructure
```

---

## Что НЕ меняется

- Синтаксис языка NODUS — ни одного символа
- Логика runtime — ни одной строки кода
- Публичное API CLI — все команды остаются
- Тесты — только обновить пути импортов

---

## Будущее разделение на репозитории

Когда проект созреет, разделение будет тривиальным:

```
packages/spec/     →  github.com/nodus-lang/spec
packages/runtime/  →  github.com/nodus-lang/runtime  (PyPI: nodus-lang)
packages/vscode/   →  github.com/nodus-lang/vscode   (Marketplace)
packs/             →  github.com/nodus-lang/packs
```

Каждая папка уже является самодостаточным пакетом.
