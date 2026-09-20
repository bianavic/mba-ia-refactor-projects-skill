# Estrutura Final do Projeto

[← README](../README.md) · [Análise Manual](manual-analysis.md) · [Design da Skill](skill-design.md) · [Resultados](results.md) · [Evolução do Uso de IA](ai-evolution.md) · [Enunciado Original](challenge-original.md)

> Este documento é **gerado**: o bloco abaixo é reescrito por `scripts/sync-docs.sh`
> a partir de `git ls-tree <primeiro-commit>` e `git ls-files`. O mesmo bloco é injetado
> na [seção 3.2 do README](../README.md#32-comparação-antes-e-depois), que é onde o
> requisito **C2** do enunciado é cumprido. Não edite à mão.

<!-- BEGIN:project-trees -->
#### Projeto 1 — `code-smells-project`

<table><tr><th>Antes (boilerplate)</th><th>Depois (refatorado)</th></tr><tr><td>

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
│           │   └── verification-recipes.md
│           └── scripts/
│               └── arch-check.sh
├── README.md
├── app.py
├── arch-check.sh
├── config/
│   └── settings.py
├── controllers/
│   ├── __init__.py
│   ├── admin_controller.py
│   ├── order_controller.py
│   ├── product_controller.py
│   ├── system_controller.py
│   └── user_controller.py
├── manual-tests.sh
├── middlewares/
│   ├── __init__.py
│   ├── auth.py
│   └── error_handler.py
├── models/
│   ├── __init__.py
│   ├── admin_model.py
│   ├── db.py
│   ├── order_model.py
│   ├── product_model.py
│   └── user_model.py
├── requirements.txt
├── routes/
│   ├── __init__.py
│   └── routes.py
└── utils/
    ├── __init__.py
    └── pagination.py
```

</td></tr></table>

#### Projeto 2 — `ecommerce-api-legacy`

<table><tr><th>Antes (boilerplate)</th><th>Depois (refatorado)</th></tr><tr><td>

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
│           │   └── verification-recipes.md
│           └── scripts/
│               └── arch-check.sh
├── .env.example
├── .gitignore
├── README.md
├── api.http
├── arch-check.sh
├── internal-tests.js
├── manual-tests.sh
├── package-lock.json
├── package.json
└── src/
    ├── app.js
    ├── config/
    │   └── index.js
    ├── controllers/
    │   ├── checkoutController.js
    │   ├── reportController.js
    │   └── userController.js
    ├── database/
    │   └── connection.js
    ├── errors/
    │   └── AppError.js
    ├── middlewares/
    │   ├── asyncHandler.js
    │   ├── errorHandler.js
    │   ├── notFoundHandler.js
    │   └── validators.js
    ├── models/
    │   ├── auditLogModel.js
    │   ├── courseModel.js
    │   ├── enrollmentModel.js
    │   ├── paymentModel.js
    │   └── userModel.js
    ├── routes/
    │   └── index.js
    ├── server.js
    ├── services/
    │   ├── checkoutService.js
    │   ├── paymentGatewayService.js
    │   ├── reportService.js
    │   └── userService.js
    └── utils/
        ├── crypto.js
        └── logger.js
```

</td></tr></table>

#### Projeto 3 — `task-manager-api`

<table><tr><th>Antes (boilerplate)</th><th>Depois (refatorado)</th></tr><tr><td>

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
│           │   └── verification-recipes.md
│           └── scripts/
│               └── arch-check.sh
├── .env.example
├── README.md
├── app.py
├── arch-check.sh
├── config/
│   ├── __init__.py
│   └── settings.py
├── controllers/
│   ├── __init__.py
│   ├── task_controller.py
│   └── user_controller.py
├── database.py
├── manual-tests.sh
├── middlewares/
│   ├── __init__.py
│   ├── auth.py
│   └── error_handler.py
├── models/
│   ├── __init__.py
│   ├── category.py
│   ├── task.py
│   └── user.py
├── requirements.txt
├── routes/
│   ├── __init__.py
│   ├── meta_routes.py
│   ├── report_routes.py
│   ├── task_routes.py
│   └── user_routes.py
├── seed.py
├── services/
│   ├── __init__.py
│   ├── authorization.py
│   ├── report_service.py
│   └── token_service.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_task_controller.py
│   └── test_user_controller.py
└── utils/
    ├── __init__.py
    └── helpers.py
```

</td></tr></table>

<sub>Gerado por `scripts/sync-docs.sh` (`git ls-tree 6d1ce6248c3e956801010a89d8bdaab48029bf30` vs. `git ls-files`). Não edite à mão.</sub>
<!-- END:project-trees -->
