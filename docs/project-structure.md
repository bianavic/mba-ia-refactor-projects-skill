# Estrutura dos Projetos — Antes e Depois

[← README](../README.md)

Árvores de arquivos de cada projeto: a versão original, que faz parte do boilerplate do desafio,
contra a versão refatorada.
Gerado por `.claude/scripts/sync-docs.sh` — não edite à mão.

<!-- BEGIN:project-trees -->
#### `code-smells-project` (refatorado)

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
├── .arch-check.conf
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
├── .env.example
├── .python-version
├── README.md
├── api-test.sh
├── app.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── controllers/
│   ├── __init__.py
│   ├── admin_controller.py
│   ├── pedido_controller.py
│   ├── produto_controller.py
│   ├── relatorio_controller.py
│   ├── sistema_controller.py
│   └── usuario_controller.py
├── database/
│   ├── __init__.py
│   └── connection.py
├── errors/
│   ├── __init__.py
│   ├── exceptions.py
│   └── handlers.py
├── middleware/
│   ├── __init__.py
│   └── auth.py
├── models/
│   ├── __init__.py
│   ├── pedido_model.py
│   ├── produto_model.py
│   └── usuario_model.py
├── requirements.txt
├── routes/
│   ├── __init__.py
│   ├── admin_routes.py
│   ├── pedido_routes.py
│   ├── produto_routes.py
│   ├── relatorio_routes.py
│   ├── sistema_routes.py
│   └── usuario_routes.py
├── services/
│   ├── __init__.py
│   ├── admin_service.py
│   ├── notificacao_service.py
│   ├── pedido_service.py
│   └── usuario_service.py
└── utils/
    ├── __init__.py
    ├── mascaramento.py
    ├── paginacao.py
    └── seguranca.py
```

</td></tr></table>

#### `ecommerce-api-legacy` (refatorado)

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
├── .env.example
├── README.md
├── api-test.sh
├── api.http
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
    │   ├── connection.js
    │   └── schema.js
    ├── errors/
    │   ├── AppError.js
    │   └── errorHandler.js
    ├── middleware/
    │   └── requireAdmin.js
    ├── models/
    │   ├── auditLogModel.js
    │   ├── courseModel.js
    │   ├── enrollmentModel.js
    │   ├── paymentModel.js
    │   └── userModel.js
    ├── routes/
    │   ├── adminRoutes.js
    │   ├── checkoutRoutes.js
    │   └── userRoutes.js
    ├── services/
    │   ├── checkoutService.js
    │   ├── paymentGatewayService.js
    │   ├── reportService.js
    │   └── userService.js
    └── utils/
        ├── asyncHandler.js
        ├── logger.js
        └── password.js
```

</td></tr></table>

#### `task-manager-api` (refatorado)

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
├── .env.example
├── .python-version
├── README.md
├── api-test.sh
├── app.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── controllers/
│   ├── __init__.py
│   ├── auth_controller.py
│   ├── category_controller.py
│   ├── report_controller.py
│   ├── system_controller.py
│   ├── task_controller.py
│   └── user_controller.py
├── database/
│   ├── __init__.py
│   └── connection.py
├── errors/
│   ├── __init__.py
│   ├── exceptions.py
│   └── handlers.py
├── middleware/
│   ├── __init__.py
│   └── auth.py
├── models/
│   ├── __init__.py
│   ├── category.py
│   ├── task.py
│   └── user.py
├── requirements.txt
├── routes/
│   ├── __init__.py
│   ├── category_routes.py
│   ├── report_routes.py
│   ├── system_routes.py
│   ├── task_routes.py
│   └── user_routes.py
├── seed.py
├── services/
│   ├── __init__.py
│   ├── category_service.py
│   ├── report_service.py
│   ├── task_service.py
│   └── user_service.py
└── utils/
    ├── __init__.py
    ├── helpers.py
    ├── pagination.py
    └── security.py
```

</td></tr></table>

<!-- END:project-trees -->
