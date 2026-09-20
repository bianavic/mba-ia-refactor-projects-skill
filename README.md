# Refatoração Arquitetural Automatizada com Skills

Entrega do desafio de MBA: a skill **`refactor-arch`**, que audita um backend legado,
classifica os problemas por severidade e o refatora para MVC — executada em 3 projetos
de stacks diferentes (Python/Flask com SQLite cru, Node.js/Express, Python/Flask com
SQLAlchemy).

O enunciado original está preservado em [`docs/challenge-original.md`](docs/challenge-original.md).

```
code-smells-project/     Projeto 1 — Python/Flask, SQLite cru    (e-commerce)
ecommerce-api-legacy/    Projeto 2 — Node.js/Express, sqlite3    (LMS/e-learning)
task-manager-api/        Projeto 3 — Python/Flask + SQLAlchemy   (task manager)
reports/                 relatórios de auditoria (saída da Fase 2)
evidence/                screenshots e logs das aplicações rodando
docs/                    deep dives e o enunciado original
scripts/                 sync-docs.sh — regenera as tabelas e árvores deste README
```

## Sumário

- [Conformidade com o enunciado](#conformidade-com-o-enunciado)
- [1. Análise Manual](#1-análise-manual)
- [2. Construção da Skill](#2-construção-da-skill)
- [3. Resultados](#3-resultados)
  - [3.1 Resumo das Auditorias](#31-resumo-das-auditorias)
  - [3.2 Comparação Antes e Depois](#32-comparação-antes-e-depois)
  - [3.3 Checklist de Validação Preenchido](#33-checklist-de-validação-preenchido)
  - [3.4 Evidências de Execução](#34-evidências-de-execução)
  - [3.5 Comportamento entre Diferentes Stacks](#35-comportamento-entre-diferentes-stacks)
  - [3.6 Limitações Conhecidas e Melhorias Futuras](#36-limitações-conhecidas-e-melhorias-futuras)
- [4. Como Executar](#4-como-executar)
  - [4.1 Pré-requisitos](#41-pré-requisitos)
  - [4.2 Comandos por Projeto](#42-comandos-por-projeto)
  - [4.3 Validação](#43-validação)
- [Critérios de Aceite](#critérios-de-aceite)
- [Manutenção da documentação](#manutenção-da-documentação)

## Conformidade com o Enunciado

Cada item exigido em ["README.md deve conter"](docs/challenge-original.md#readmemd-deve-conter) está completo neste próprio README — nenhum item obrigatório fica só em `docs/`.

| Requisito | Onde está |
|---|---|
| **A1.** Lista dos problemas identificados manualmente em cada projeto | [1. Análise Manual](#1-análise-manual) |
| **A2.** Classificação por severidade | [1. Análise Manual](#1-análise-manual) |
| **A3.** Justificativa de por que cada problema é relevante | [1. Análise Manual](#1-análise-manual) |
| **B1.** Decisões de design do `SKILL.md` e dos arquivos de referência | [2. Construção da Skill](#2-construção-da-skill) |
| **B2.** Anti-patterns incluídos no catálogo e por quê | [2. Construção da Skill](#2-construção-da-skill) |
| **B3.** Como garantiu que a skill é agnóstica de tecnologia | [2. Construção da Skill](#2-construção-da-skill) |
| **B4.** Desafios encontrados e como resolveu | [2. Construção da Skill](#2-construção-da-skill) |
| **C1.** Resumo dos relatórios de auditoria dos 3 projetos | [3.1 Resumo das Auditorias](#31-resumo-das-auditorias) |
| **C2.** Comparação antes/depois da estrutura de cada projeto | [3.2 Comparação Antes e Depois](#32-comparação-antes-e-depois) |
| **C3.** Checklist de validação preenchido para cada projeto | [3.3 Checklist de Validação Preenchido](#33-checklist-de-validação-preenchido) |
| **C4.** Screenshots ou logs das aplicações rodando após refatoração | [3.4 Evidências de Execução](#34-evidências-de-execução) |
| **C5.** Observações sobre o comportamento em stacks diferentes | [3.5 Comportamento entre Diferentes Stacks](#35-comportamento-entre-diferentes-stacks) |
| **D1.** Pré-requisitos (ferramenta instalada e configurada) | [4.1 Pré-requisitos](#41-pré-requisitos) |
| **D2.** Comandos para executar a skill em cada projeto | [4.2 Comandos por Projeto](#42-comandos-por-projeto) |
| **D3.** Como validar que a refatoração funcionou | [4.3 Validação](#43-validação) |

**Critérios de Aceite** ([enunciado 9.7](docs/challenge-original.md#97-critérios-de-aceite)) — obrigatórios nos 3 projetos, sem exceção: ver a [seção dedicada](#critérios-de-aceite), mantida por `/sync-docs` a cada rodada.

## Visão Geral

`refactor-arch` executa 3 fases sequenciais em qualquer projeto backend:

1. **Análise** — detecta linguagem, framework, banco de dados e arquitetura atual, sem assumir nada previamente.
2. **Auditoria** — cruza o código contra um catálogo de 16 anti-patterns, gera um relatório por severidade e **para para confirmação humana** antes de tocar em qualquer arquivo.
3. **Refatoração** — reestrutura o projeto para MVC (adaptando camadas já existentes, quando aplicável), preservando 100% do comportamento observável, e valida o resultado.

```
mba-ia-refactor-projects-skill/
├── README.md
├── docs/                       # deep dives — ver Documentação
├── code-smells-project/        # Projeto 1 — Python/Flask (E-commerce)
├── ecommerce-api-legacy/       # Projeto 2 — Node.js/Express (LMS)
├── task-manager-api/           # Projeto 3 — Python/Flask (Task Manager)
├── reports/                    # saída da Fase 2 de cada projeto
└── evidence/                   # screenshots + logs (seção 3.4)
```

Árvore completa em [`docs/project-structure.md`](docs/project-structure.md).

A skill (`SKILL.md` + `references/` + `scripts/`) vive **idêntica** dentro dos 3 projetos, em `.claude/skills/refactor-arch/` — exigência do enunciado, não duplicação acidental. Cada finding do relatório de Fase 2 referencia um `AP-xx` do catálogo; cada `AP-xx` é resolvido por um ou mais `RP-xx` do playbook de refatoração — esse mapeamento cruzado é o que permite a Fase 3 aplicar a correção certa mecanicamente, sem reinventar a solução a cada execução (detalhe em [2. Construção da Skill](#2-construção-da-skill)).

## 1. Análise Manual

Leitura manual dos 3 projetos **antes** de escrever a skill: **21 achados, 7 por projeto**,
classificados pela [escala de severidade do enunciado](docs/challenge-original.md#definição-de-severidades).
Vários foram confirmados executando as aplicações, não só lendo o código.

O detalhamento de cada achado (descrição completa, linhas exatas e validação em execução)
está em [`docs/manual-analysis.md`](docs/manual-analysis.md).

### Projeto 1 — `code-smells-project`

Flask 3.1.1 + SQLite cru · e-commerce · 4 arquivos, ~600 linhas, sem separação de camadas.
**CRITICAL: 2 · HIGH: 1 · MEDIUM: 2 · LOW: 2**

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | SQL Injection generalizada | `models.py` (~20 pontos) | Qualquer campo controlado pelo cliente permite ler, alterar ou destruir dados arbitrariamente — o problema de maior impacto do projeto. |
| CRITICAL | Segredo hardcoded e vazado em `/health` | `app.py:7-8`, `controllers.py:285-289` | O segredo usado para assinar sessões fica público no repositório **e** na própria API — invalida a integridade de sessão. |
| HIGH | God Class / ausência total de MVC | `models.py`, `controllers.py` | Impossível testar uma regra isoladamente; mudar um domínio arrisca quebrar os outros três no mesmo arquivo. |
| MEDIUM | N+1 no histórico de pedidos | `models.py:171-233` | Uma única listagem pode disparar dezenas de queries; degrada com o crescimento da base. |
| MEDIUM | Ausência de paginação | `controllers.py:5-12,128-134,229-235` | Gargalo de performance e payload que só piora à medida que a base cresce. |
| LOW | `print()` como logging | `controllers.py`, `app.py:56,83-86` | Sem níveis, sem estrutura, sem rotação — inviável em produção. |
| LOW | Categorias válidas hardcoded inline | `controllers.py:52` | Qualquer categoria nova exige alterar código-fonte em vez de configuração. |

### Projeto 2 — `ecommerce-api-legacy`

Node.js + Express 4.18.2 (lockfile 4.22.1) + `sqlite3` 5.1.7 · LMS/e-learning · 3 arquivos, ~180 linhas, sem camadas.
**CRITICAL: 2 · HIGH: 1 · MEDIUM: 2 · LOW: 2**

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | Segredos de produção hardcoded | `utils.js:2-6` | Uma chave de gateway de pagamento "live" vazada no repositório é um incidente imediato, não hipotético. |
| CRITICAL | Hashing de senha falso (base64 reversível) | `utils.js:17-23` | Equivale a senha em claro com verniz cosmético; qualquer vazamento expõe todas as credenciais. |
| HIGH | God Class | `AppManager.js:1-142` | Arquitetura, roteamento e regra de negócio no mesmo lugar — impossível testar em isolamento. |
| MEDIUM | N+1 em cascata de callbacks no relatório financeiro | `AppManager.js:80-129` | Tempo de resposta cresce multiplicativamente com cursos × matrículas; origem do "callback hell". |
| MEDIUM | Estado mutável global | `utils.js:9-10` | Fonte clássica de race conditions em runtime concorrente. |
| LOW | `console.log` como logging | `utils.js:13`, `AppManager.js:45` | Mesma limitação do projeto 1: sem structured logging. |
| LOW | Mistura de idiomas inconsistente | `AppManager.js` | Problema de padronização/manutenibilidade, não funcional. |

### Projeto 3 — `task-manager-api`

Flask + Flask-SQLAlchemy + SQLite · task manager · já tem `models/routes/services/utils`,
mas a separação é só estrutural — a disciplina por camada não é respeitada.
**CRITICAL: 2 · HIGH: 1 · MEDIUM: 2 · LOW: 2**

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | Hashing de senha fraco e sem salt (MD5) | `models/user.py:27-31` | MD5 é quebrado e, sem salt, trivialmente atacável por rainbow tables. |
| CRITICAL | Hash de senha vazado em toda resposta de API | `models/user.py:16-25` | Expõe material sensível a qualquer cliente; combinado ao MD5, facilita ataque offline. |
| HIGH | Regra "task atrasada" duplicada em vez de centralizada | `models/task.py:50-60` + 3 rotas | Risco real de a regra divergir silenciosamente se só um ponto for corrigido. |
| MEDIUM | Camada de serviço morta / nunca conectada | `services/notification_service.py` | Código morto que engana quem lê a estrutura de pastas achando que a feature existe. |
| MEDIUM | Ausência de paginação | `routes/task_routes.py`, `user_routes.py`, `report_routes.py` | Mesmo problema de performance dos outros dois, agravado pelo N+1 do relatório. |
| LOW | `print()` como logging | `routes/*`, `services/notification_service.py` | Padrão recorrente nos 3 projetos — sem níveis, sem estrutura. |
| LOW | Imports não utilizados | `routes/task_routes.py:7`, `app.py:7` | Ruído que dificulta entender as dependências reais de cada arquivo. |

**Observação transversal:** os 3 projetos convergem para os mesmos grupos de problema apesar de stacks e níveis de organização diferentes — segredo hardcoded e senha em claro/hash quebrado nos 3, vazamento de dado sensível via serialização nos 3, N+1 e paginação ausente nos 3, `print()`/`console.log` como logging nos 3. Essa repetição é o que moldou o catálogo de anti-patterns (seção 2) como sinais agnósticos de linguagem, não regras específicas de Flask ou Express.

## 2. Construção da Skill

```
.claude/skills/refactor-arch/
├── SKILL.md                     # fluxo das 3 fases (carregado sempre)
├── references/                  # carregados sob demanda, por fase
│   ├── project-analysis.md          # Fase 1
│   ├── anti-patterns-catalog.md     # Fase 2
│   ├── audit-report-template.md     # Fase 2
│   ├── architecture-guidelines.md   # Fase 3
│   ├── refactoring-playbook.md      # Fase 3
│   └── verification-recipes.md      # Fase 3, passo 6
└── scripts/arch-check.sh        # checagem estrutural AP-16, empacotada
```

**Decisões de design.** O `SKILL.md` segue *progressive disclosure*: funciona como índice/prompt enxuto e cada arquivo de referência só é lido quando a fase correspondente começa — a Fase 1 nunca carrega o playbook de refatoração. A `description` do frontmatter foi escrita em inglês para casar com a forma como o usuário pediria a tarefa ("analyze, audit, or refactor a project's architecture"), já que a invocação é dirigida por similaridade semântica. Cada `references/*.md` cobre uma das 5 áreas de conhecimento obrigatórias do enunciado (análise de projeto, catálogo, template de relatório, guidelines de arquitetura, playbook); `verification-recipes.md` foi adicionado depois, fora dessas 5, para dar suporte à checagem mecânica do passo 6 da Fase 3. Decisões completas, incluindo o conteúdo de cada arquivo, em [`docs/skill-design.md`](docs/skill-design.md).

**Catálogo de anti-patterns (16 entradas, acima do mínimo de 8):**

- **CRITICAL (4):** AP-01 SQL Injection · AP-02 Segredos hardcoded · AP-03 Hashing quebrado/falso · AP-04 Dado sensível vazado via serialização.
- **HIGH (4):** AP-05 God Class · AP-06 Lógica duplicada · AP-07 Estado mutável global · AP-16 Persistência/ORM chamada direto na rota.
- **MEDIUM (4):** AP-08 N+1 · AP-09 Ausência de paginação · AP-10 Código morto/desconectado · AP-11 API deprecated.
- **LOW (4):** AP-12 Logging via print/console · AP-13 Configuração hardcoded · AP-14 Imports não usados · AP-15 Idioma/nomenclatura inconsistente.

Os 15 primeiros entraram porque apareceram, na prática, em pelo menos um dos 3 projetos durante a análise manual — nenhum é hipotético. O AP-16 entrou depois, pelo motivo oposto: um problema real que ficou no `task-manager-api` e atravessou a auditoria original justamente por não estar catalogado (postmortem completo em [`docs/results.md`](docs/results.md#bug-encontrado-após-a-entrega)).

**Agnosticismo de tecnologia**, três decisões: (1) detecção, nunca suposição — a Fase 1 infere a stack a cada execução, nunca assume Python/Flask; (2) sinais de detecção descritos por *padrão* ("query montada por concatenação com valor do cliente"), não por sintaxe de uma linguagem; (3) playbook com exemplo antes/depois nas duas linguagens quando aplicável, e instrução explícita para aplicar "o mesmo princípio" numa stack sem exemplo. A prova concreta é a execução real nos 3 projetos deste repositório, em três stacks diferentes, sem qualquer alteração na skill entre uma execução e outra.

**Desafios e soluções:**
- **Risco de finding fabricado:** regra mais repetida em todos os arquivos — "nunca reportar um finding sem arquivo/linha real". Os 3 relatórios em `reports/` citam ranges de linha verificáveis.
- **Projeto parcialmente em camadas exigindo tratamento diferente de um monolito:** `architecture-guidelines.md` trata isso como categoria própria ("Partially-layered projects") — manter nomes de pasta existentes, só corrigir responsabilidades dentro deles.
- **Preservar comportamento mesmo corrigindo falhas de segurança:** redigir o hash de senha da resposta é, por definição, mudança de response shape — mas desejada. Documentada como exceção explícita em `architecture-guidelines.md`.
- **Tornar a Fase 3 mecânica, não ad hoc:** o mapeamento cruzado `AP-xx ↔ RP-xx` permite que a Fase 3 leia a `Recommendation` do finding confirmado e aplique o `RP-xx` citado, sem depender do agente "lembrar" a correção certa a cada execução.

## 3. Resultados

### 3.1 Resumo das Auditorias

Narrativa completa em [`reports/`](reports/). Cada execução da Fase 2 gera um arquivo
novo (`audit-project-<N>-part<M>.md`) — relatórios anteriores nunca são sobrescritos,
porque são a evidência do estado "antes".

<!-- BEGIN:audit-summary -->
| # | Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | `code-smells-project` | Python / Flask 3.1.1 | 0 | 1 | 1 | 0 | **2** | [`audit-project-1-part4.md`](reports/audit-project-1-part4.md) |
| 2 | `ecommerce-api-legacy` | JavaScript / Node.js 26 + Express 4.22.1, sqlite3 6.0.1 | 1 | 0 | 0 | 2 | **3** | [`audit-project-2-part4.md`](reports/audit-project-2-part4.md) |
| 3 | `task-manager-api` | Python / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 | 0 | 3 | 4 | 4 | **11** | [`audit-project-3-part3.md`](reports/audit-project-3-part3.md) |

<sub>Gerado por `scripts/sync-docs.sh` a partir de `reports/`. Não edite à mão.</sub>
<!-- END:audit-summary -->

### 3.2 Comparação Antes e Depois

Estrutura de cada projeto antes da Fase 3 (boilerplate do commit inicial do desafio) e
depois (estado atual), geradas por `scripts/sync-docs.sh` a partir de `git ls-tree` e
`git ls-files` — nunca editadas à mão. O mesmo bloco também está em
[`docs/project-structure.md`](docs/project-structure.md).

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
├── api-tests.http
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
├── api-tests.http
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
├── api-tests.http
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

### 3.3 Checklist de Validação Preenchido

Checklist do [enunciado 9.4](docs/challenge-original.md#94-requisitos), preenchido para os 3 projetos após a Fase 3 — cada célula é verificável no repositório (relatório, evidência ou arquivo citado):

| Item | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Linguagem detectada | ✓ Python | ✓ JavaScript/Node.js | ✓ Python |
| Framework detectado | ✓ Flask 3.1.1 | ✓ Express 4.22.1 (Node 26) | ✓ Flask 3.0.0 + SQLAlchemy 3.1.1 |
| Domínio descrito | ✓ E-commerce | ✓ LMS/checkout | ✓ Task Manager |
| Nº de arquivos condiz | ✓ 16 arquivos (rodada 3) | ✓ 17 arquivos (rodada 3) | ✓ 22 arquivos (rodada 3) |
| Relatório segue o template | ✓ ⁵ | ✓ ¹ | ✓ |
| Finding com arquivo/linha exatos | ✓ | ✓ | ✓ |
| Ordenado CRITICAL → LOW | ✓ | ✓ | ✓ |
| Mínimo de 5 findings | ✓ 5 (rodada 3) ⁷ | ✓ 16 (rodada 3) ⁶ | ✓ 11 (rodada 3) |
| Detecção de API deprecated (se aplicável) | – n/a | – n/a | ✓ `datetime.utcnow()` ×18 (rodada 1) |
| Pausa e pede confirmação antes da Fase 3 | ✓ | ✓ | ✓ |
| Estrutura de diretórios segue MVC | ✓ | ✓ | ✓ camadas existentes ajustadas ² |
| Configuração extraída (sem hardcoded) | ✓ `config/settings.py` | ✓ `src/config/index.js` | ✓ `config/settings.py` |
| Models abstraem dados | ✓ | ✓ | ✓ |
| Views/Routes separadas | ✓ | ✓ | ✓ |
| Controllers concentram o fluxo | ✓ | ✓ controllers finos + `services/` de domínio | ✓ `controllers/` ³ |
| Error handling centralizado | ✓ `middlewares/error_handler.py` | ✓ `src/middlewares/errorHandler.js` | ✓ `middlewares/error_handler.py` ⁴ |
| Entry point claro | ✓ `app.py` | ✓ `src/server.js` (o `app.js` monta, sem efeito colateral) | ✓ `app.py` |
| Aplicação inicia sem erros | ✓ `evidence/project1-boot.png` | ✓ `evidence/project2-boot.png` + log da rodada 3 | ✓ `evidence/project3-boot.png` |
| Endpoints originais respondem | ✓ | ✓ `manual-tests.sh` na rodada 3 | ✓ |

As 7 notas de rodapé narrativas (¹⁻⁴ acima, incluindo o achado de `admin_controller.py` que motivou a re-auditoria ⁵, e o status pendente das rodadas 4 de `ecommerce-api-legacy` ⁶ e `code-smells-project` ⁷) estão em [`docs/results.md`](docs/results.md#checklist-de-validação-preenchido).

### 3.4 Evidências de Execução

![Boot do code-smells-project sem SECRET_KEY exposta](evidence/project1-boot.png)
![Boot do ecommerce-api-legacy](evidence/project2-boot.png)
![Boot do task-manager-api](evidence/project3-boot.png)

Galeria completa (10 screenshots: senha não vazada, admin bloqueado, checkout sem cartão em claro, token de login assinado, paginação) e **logs de terminal reais** dos 3 `manual-tests.sh` e dos 3 `arch-check.sh`, em [`docs/results.md`](docs/results.md#evidências-de-execução). As validações mais recentes — boot, `arch-check.sh`, um `curl` por finding corrigido e a suíte completa, todas capturadas com a aplicação de pé — estão em [`evidence/logs/code-smells-project-round3-validation.txt`](evidence/logs/code-smells-project-round3-validation.txt) (Projeto 1, rodada 3), [`evidence/logs/ecommerce-api-legacy-round3-validation.txt`](evidence/logs/ecommerce-api-legacy-round3-validation.txt) (Projeto 2, rodada 3 — inclui o detector do `arch-check` validado contra uma violação plantada e a saída de `npm run test:internal`) e dois logs do Projeto 3 — estrutura MVC/AP-16 em [`evidence/logs/task-manager-api-round3-validation.txt`](evidence/logs/task-manager-api-round3-validation.txt) e autenticação/autorização (boot com/sem `SECRET_KEY`, tokens forjados e de contas apagadas/inativas rejeitados, `pytest` 67/67) em [`evidence/logs/task-manager-api-round4-validation.txt`](evidence/logs/task-manager-api-round4-validation.txt). A skill rodando de ponta a ponta tem duas capturas complementares: [`item1-2-skill-phase1-phase2-gate-code-smells-project.txt`](evidence/logs/item1-2-skill-phase1-phase2-gate-code-smells-project.txt) (Projeto 1, modo headless e somente leitura, parando na pergunta do gate) e [`item1-2-skill-3-fases-gate-respondido-ecommerce-api-legacy.txt`](evidence/logs/item1-2-skill-3-fases-gate-respondido-ecommerce-api-legacy.txt) (Projeto 2, execução interativa com o gate **respondido** e a Fase 3 executando). O inventário completo — o que cada screenshot e cada log mostram, e quais foram capturados antes da última rodada — está em [`docs/results.md`](docs/results.md#evidências-de-execução); as lacunas remanescentes, em [Lacunas de Evidência](docs/results.md#lacunas-de-evidência).

### 3.5 Comportamento entre Diferentes Stacks

A mesma skill, sem qualquer alteração, produziu relatórios e refatorações corretos em Python/Flask monolítico, Node.js/Express monolítico e Python/Flask parcialmente em camadas — a única diferença entre as 3 execuções foi o conteúdo do relatório e da refatoração, nunca o processo (`claude "/refactor-arch"` e o mesmo `SKILL.md` nos 3 casos). Detalhe rodada a rodada em [`docs/results.md`](docs/results.md#comportamento-entre-diferentes-stacks).

### 3.6 Limitações Conhecidas e Melhorias Futuras

Não faz parte do escopo obrigatório do desafio, mas ficou evidente durante a auditoria manual do
Projeto 2 e vale registrar para uma próxima iteração deste repositório:

- **Sem branch protection no `main`.** Confirmado via `gh api repos/.../branches/main/protection`
  → `404 Branch not protected`. Nenhum PR é obrigado a passar por review ou por um check antes do
  merge.
- **Sem CI/CD.** Não existe `.github/workflows/` — nenhum pipeline roda em PR, então não há
  execução automática de `arch-check.sh`/`manual-tests.sh`/testes unitários nem de um scanner de
  segredos antes do merge.
- **Sem scanner de segredos automatizado.** O único mecanismo existente é o `.gitignore`
  (raiz e `ecommerce-api-legacy/.gitignore`), que exclui `.env`, `*.db`, `node_modules/`,
  `instance/` — mas isso só impede que certos *tipos de arquivo* entrem no repo. Não pega segredo
  hardcoded dentro do código-fonte (`.js`/`.py`), que foi exatamente a classe de achado CRITICAL
  da rodada 1 em ambos os Projetos 1 e 2 (`SECRET_KEY`/`dbPass`/`pk_live_...` como string literal
  em arquivo versionado).
- Hoje, a única coisa que impede um segredo real de chegar ao `main` é revisão humana manual —
  sem nenhum gate técnico forçando essa revisão a acontecer.

Melhoria proposta: adicionar um workflow do GitHub Actions rodando um scanner de segredos
(`gitleaks` ou `trufflehog`) em todo PR, e habilitar branch protection no `main` exigindo esse
check (e ao menos 1 review) antes do merge.

## 4. Como Executar

### 4.1 Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`) — a skill deste repositório está no formato dele (`.claude/skills/refactor-arch/`). Gemini CLI e OpenAI Codex também são aceitos pelo enunciado; nesse caso, adapte o comando de invocação e o path da skill para a convenção da ferramenta escolhida — o conteúdo de `references/` permanece o mesmo.
- **code-smells-project** e **task-manager-api**: Python 3.10+ (`pip install -r requirements.txt`).
- **ecommerce-api-legacy**: Node.js 18+ (`npm install`).
- A skill já está presente em `.claude/skills/refactor-arch/` **dentro de cada projeto** —
  nada a instalar, basta abrir o Claude Code na pasta do projeto

> Projetos 1 e 3 sobem na mesma porta 5000: rode um por vez, ou sobrescreva `PORT`/`FLASK_PORT`.

### 4.2 Comandos por Projeto

```bash
# Projeto 1 — Python/Flask, SQLite cru
cd code-smells-project && claude "/refactor-arch"

# Projeto 2 — Node.js/Express
cd ecommerce-api-legacy && claude "/refactor-arch"

# Projeto 3 — Python/Flask + SQLAlchemy
cd task-manager-api && claude "/refactor-arch"
```

A skill roda as 3 fases em sequência e **pausa depois da Fase 2**, pedindo confirmação
explícita antes de tocar em qualquer arquivo. O relatório da Fase 2 é salvo
automaticamente em `reports/` na raiz do repositório.

**Subir cada aplicação** (para ver o resultado da Fase 3 rodando, fora da skill):

| Projeto | Comando | Porta |
|---|---|---|
| `code-smells-project` | `pip install -r requirements.txt && python app.py` | `5000` |
| `ecommerce-api-legacy` | `npm install && npm start` | `3000` (`PORT=3100 npm start` se ocupada) |
| `task-manager-api` | `pip install -r requirements.txt && cp .env.example .env && python seed.py && python app.py` | `5000` |

`task-manager-api` precisa do `seed.py` antes do primeiro boot (senão os endpoints devolvem listas vazias) e falha ao subir sem `SECRET_KEY` no `.env` — o `.env.example` já traz `FLASK_ENV=development`, que dispensa configurar uma chave real para teste local. Detalhes completos (variáveis, seeds, exemplos de requisição) ficam no `README.md` de cada projeto.

### 4.3 Validação

```bash
# 1. estrutura: nenhuma rota toca persistência direto (AP-16)
cd <projeto> && ./arch-check.sh        # exit 0 = passou

# 2. a aplicação sobe e os endpoints originais respondem
#    (projeto 2 tem api.http; projetos 1 e 3, curl nos endpoints do README do projeto)

# 3. documentação em dia com os relatórios
scripts/sync-docs.sh --check           # exit 0 = README e docs/ refletem reports/
```

`arch-check.sh` existe em duas formas: a versão específica de cada projeto (na raiz dele)
e a versão genérica empacotada na skill (`scripts/arch-check.sh`), que detecta a stack
sozinha para projetos que ainda não têm uma. As duas checam a mesma regra (AP-16).

## Critérios de Aceite

Mínimos exigidos pelo [enunciado](docs/challenge-original.md#critérios-de-aceite) —
obrigatórios nos 3 projetos, sem exceção. Mantido por `/sync-docs`. Cada `✓` aponta para o
relatório ou a evidência que o sustenta; célula em branco significa não verificado, não "falhou".

| Critério | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Fase 1 detecta stack corretamente | ✓ Python / Flask 3.1.1 | ✓ JavaScript / Node.js 26 + Express 4.22.1, sqlite3 6.0.1 | ✓ Python / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 |
| Fase 2 encontra ≥ 5 findings | ✓ 5 ([part3](reports/audit-project-1-part3.md)) ⁷ | ✓ 16 ([part3](reports/audit-project-2-part3.md)) ⁶ | ✓ 11 ([part3](reports/audit-project-3-part3.md)) |
| Fase 2 inclui ≥ 1 CRITICAL ou HIGH | ✓ 1 CRITICAL | ✓ 1 CRITICAL + 5 HIGH | ✓ 3 HIGH |
| Fase 3 aplicação funciona após refatoração | ✓ [log rodada 3](evidence/logs/code-smells-project-round3-validation.txt) ⁷ | ✓ [log rodada 3](evidence/logs/ecommerce-api-legacy-round3-validation.txt) ⁶ | ✓ [log rodada 3](evidence/logs/task-manager-api-round3-validation.txt) + [log rodada 4](evidence/logs/task-manager-api-round4-validation.txt) |

A linha "Fase 1 detecta stack" sai da linha `Stack:` de cada relatório; as duas seguintes, da
tabela de [§3.1](#31-resumo-das-auditorias). "Aplicação funciona" só está marcada onde há registro
de execução real — boot mais endpoints respondendo. ⁶ `ecommerce-api-legacy` tem uma rodada 4
([`audit-project-2-part4.md`](reports/audit-project-2-part4.md), 2026-09-20) mais recente que a
citada aqui: achou um novo CRITICAL (ausência de autenticação/autorização em todos os endpoints),
mas parou no gate da Fase 2 — a Fase 3 não rodou, o achado segue **aberto e sem correção**, e as
duas marcações acima refletem apenas o que a rodada 3 (com Fase 3 completa) já comprova. ⁷
`code-smells-project` tem uma rodada 4 análoga
([`audit-project-1-part4.md`](reports/audit-project-1-part4.md), 2026-09-20): achou 1 HIGH + 1
MEDIUM (mutação sem checar linha afetada; coerção de tipo sem guard virando 500), também parou no
gate da Fase 2, e os dois seguem **abertos e sem correção**. Detalhe de ambas em
[`docs/results.md`](docs/results.md#checklist-de-validação-preenchido).


## Manutenção da documentação

Depois de cada rodada da skill, na raiz do repositório:

```bash
claude "/sync-docs"
```

O comando roda `scripts/sync-docs.sh` (que regenera **3.1** e **3.2** a partir de
`reports/` e do índice do git, entre os marcadores `<!-- BEGIN:... -->`), atualiza
`docs/results.md`, preenche o checklist de **3.3** e os Critérios de Aceite com o
resultado da rodada, e lista o que ficou faltando (evidência, `TODO`, relatório ausente).

Blocos entre marcadores são gerados — editá-los à mão é desfeito na próxima rodada.
