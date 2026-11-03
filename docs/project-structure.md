# Estrutura dos Projetos — Antes e Depois

[← README](../README.md)

Árvores de arquivos de cada projeto: a versão original, que faz parte do boilerplate do desafio,
contra a versão refatorada.
Gerado por `.claude/scripts/sync-docs.sh` — não edite à mão.

<!-- BEGIN:project-trees -->
#### `code-smells-project` (ainda não refatorado — as duas colunas mostram o boilerplate)

<table><tr><th>Antes (boilerplate)</th><th>Depois (árvore de trabalho)</th></tr><tr><td>

```
code-smells-project/
├── README.md
├── app.py
├── controllers.py
├── database.py
├── models.py
└── requirements.txt
```

</td><td>

```
code-smells-project/
├── .claude/
│   └── skills/
│       └── refactor-arch/
│           ├── SKILL.md
│           ├── references/
│           │   ├── anti-patterns-catalog.md
│           │   ├── architecture-guidelines.md
│           │   ├── audit-report-template.md
│           │   ├── project-analysis.md
│           │   ├── refactoring-playbook.md
│           │   └── refactoring-validation.md
│           └── scripts/
│               ├── arch-check.sh
│               └── completion-box.sh
├── README.md
├── app.py
├── controllers.py
├── database.py
├── models.py
└── requirements.txt
```

</td></tr></table>

#### `ecommerce-api-legacy` (ainda não refatorado — as duas colunas mostram o boilerplate)

<table><tr><th>Antes (boilerplate)</th><th>Depois (árvore de trabalho)</th></tr><tr><td>

```
ecommerce-api-legacy/
├── README.md
├── api.http
├── package-lock.json
├── package.json
└── src/
    ├── AppManager.js
    ├── app.js
    └── utils.js
```

</td><td>

```
ecommerce-api-legacy/
├── .claude/
│   └── skills/
│       └── refactor-arch/
│           ├── SKILL.md
│           ├── references/
│           │   ├── anti-patterns-catalog.md
│           │   ├── architecture-guidelines.md
│           │   ├── audit-report-template.md
│           │   ├── project-analysis.md
│           │   ├── refactoring-playbook.md
│           │   └── refactoring-validation.md
│           └── scripts/
│               ├── arch-check.sh
│               └── completion-box.sh
├── README.md
├── api.http
├── package-lock.json
├── package.json
└── src/
    ├── AppManager.js
    ├── app.js
    └── utils.js
```

</td></tr></table>

#### `task-manager-api` (ainda não refatorado — as duas colunas mostram o boilerplate)

<table><tr><th>Antes (boilerplate)</th><th>Depois (árvore de trabalho)</th></tr><tr><td>

```
task-manager-api/
├── README.md
├── app.py
├── database.py
├── models/
│   ├── __init__.py
│   ├── category.py
│   ├── task.py
│   └── user.py
├── requirements.txt
├── routes/
│   ├── __init__.py
│   ├── report_routes.py
│   ├── task_routes.py
│   └── user_routes.py
├── seed.py
├── services/
│   ├── __init__.py
│   └── notification_service.py
└── utils/
    ├── __init__.py
    └── helpers.py
```

</td><td>

```
task-manager-api/
├── .claude/
│   └── skills/
│       └── refactor-arch/
│           ├── SKILL.md
│           ├── references/
│           │   ├── anti-patterns-catalog.md
│           │   ├── architecture-guidelines.md
│           │   ├── audit-report-template.md
│           │   ├── project-analysis.md
│           │   ├── refactoring-playbook.md
│           │   └── refactoring-validation.md
│           └── scripts/
│               ├── arch-check.sh
│               └── completion-box.sh
├── README.md
├── app.py
├── database.py
├── models/
│   ├── __init__.py
│   ├── category.py
│   ├── task.py
│   └── user.py
├── requirements.txt
├── routes/
│   ├── __init__.py
│   ├── report_routes.py
│   ├── task_routes.py
│   └── user_routes.py
├── seed.py
├── services/
│   ├── __init__.py
│   └── notification_service.py
└── utils/
    ├── __init__.py
    └── helpers.py
```

</td></tr></table>

<!-- END:project-trees -->
