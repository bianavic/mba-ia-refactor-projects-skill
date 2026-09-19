# Estrutura Final do Projeto

[← README](../README.md) · [Análise Manual](manual-analysis.md) · [Design da Skill](skill-design.md) · [Resultados](results.md) · [Evolução do Uso de IA](ai-evolution.md) · [Enunciado Original](challenge-original.md)

> Árvore completa do repositório após as 3 refatorações. A visão de primeiro nível está na [Visão Geral do README](../README.md#visão-geral).

---

```
mba-ia-refactor-projects-skill/
├── README.md
├── CLAUDE.md                              # contexto do repositório para o agente (seção 7.1)
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (E-commerce)
│   ├── .claude/skills/refactor-arch/      # SKILL.md + references/ + scripts/arch-check.sh
│   ├── CLAUDE.md                          # invariantes de segurança e validação do projeto
│   ├── app.py                             # composition root
│   ├── config/settings.py
│   ├── controllers/
│   ├── models/
│   ├── middlewares/
│   ├── routes/
│   ├── requirements.txt
│   ├── manual-tests.sh                    # curl de validação manual (seção 4.5)
│   └── arch-check.sh                      # checagem estrutural AP-16 (seções 4.5 e 5.8)
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS)
│   ├── .claude/skills/refactor-arch/      # cópia da skill
│   ├── CLAUDE.md                          # invariantes de segurança e validação do projeto
│   ├── src/
│   │   ├── app.js                         # composition root
│   │   ├── config/
│   │   ├── controllers/
│   │   ├── models/
│   │   ├── services/
│   │   ├── middlewares/
│   │   ├── routes/
│   │   └── utils/
│   ├── package.json
│   ├── manual-tests.sh                    # curl de validação manual (seção 4.5)
│   └── arch-check.sh                      # checagem estrutural AP-16 (seções 4.5 e 5.8)
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (Task Manager)
│   ├── .claude/skills/refactor-arch/      # cópia da skill
│   ├── CLAUDE.md                          # invariantes de segurança e validação do projeto
│   ├── app.py                             # composition root
│   ├── config/settings.py                 # novo
│   ├── controllers/                       # novo — task_controller.py, user_controller.py (fecha o AP-16, seção 5.8)
│   ├── middlewares/error_handler.py       # novo — handler central de erros
│   ├── models/
│   ├── routes/
│   ├── services/                          # report_service.py estendido (+ categorias); notification_service.py removido
│   ├── tests/                             # novo — pytest unitário dos controllers (task/user)
│   ├── utils/
│   ├── requirements.txt                   # inclui pytest
│   ├── manual-tests.sh                    # curl de validação manual (seção 4.5)
│   └── arch-check.sh                      # checagem estrutural AP-16 (seções 4.5 e 5.8)
│
├── reports/
│   ├── audit-project-1.md
│   ├── audit-project-1-part2.md           # re-auditoria após a Fase 3 (seção 5.9)
│   ├── audit-project-2.md
│   ├── audit-project-2-part2.md           # re-auditoria após a Fase 3
│   ├── audit-project-3.md
│   ├── audit-project-3-part2.md           # re-auditoria após a Fase 3 (seção 5.8)
│   └── audit-project-4.md                 # projeto externo Go/Gin — só Fases 1 e 2 (seção 5.6)
│
└── evidence/                              # screenshots citados na seção 4.6
    ├── project1-boot.png
    ├── project1-usuarios-sem-senha.png
    ├── project1-admin-bloqueado.png
    ├── project2-boot.png
    ├── project2-checkout-sem-cartao.png
    ├── project2-checkout-sem-cartao-log.png
    ├── project3-boot.png
    ├── project3-login-token.png
    ├── project3-users-sem-senha.png
    └── project3-tasks-paginacao.png
```
