# Structure

## Magic Spec Structure with Nodus

[Magic Spec](https://github.com/teratron/magic-spec)

```
magic-spec/  
├── .agents/
│   ├── rules/
│   ├── skills/
│   └── workflows/
│
├── .magic/              ← ядро Magic Spec
│
└── .nodus/              ← ядро Nodus
```

Или

```
magic-spec/  
├── .agents/
│   ├── rules/
│   ├── skills/
│   └── workflows/
│
└── .magic/              ← ядро Magic Spec
    └── .nodus/          ← ядро Nodus
```

## User Project Structure with Magic Spec

```
my-project/
├── .agents/
│   ├── rules/
│   ├── skills/
│   └── workflows/
│
├── .magic/              ← ядро Magic Spec
│
├── .nodus/              ← ядро Nodus
│
└── .design/             ← то что генерирует Magic Spec
```

Или

```
magic-spec/  
├── .agents/
│   ├── rules/
│   ├── skills/
│   └── workflows/
│
└── .magic/              ← ядро Magic Spec
│   └── .nodus/          ← ядро Nodus
│
└── .design/             ← то что генерирует Magic Spec
```
