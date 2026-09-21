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
evidence/                logs das aplicações rodando
docs/                    deep dives e o enunciado original
scripts/                 sync-docs.sh — regenera as tabelas e árvores deste README
```

## Sumário

- [Conformidade com o enunciado](#conformidade-com-o-enunciado)
- [Visão Geral](#visão-geral)
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
| **C1.** Resumo dos relatórios de auditoria dos 3 projetos (findings por severidade) | [3.1 Resumo das Auditorias](#31-resumo-das-auditorias) |
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
2. **Auditoria** — cruza o código contra um catálogo de 17 anti-patterns, gera um relatório por severidade e **para para confirmação humana** antes de tocar em qualquer arquivo.
3. **Refatoração** — reestrutura o projeto para MVC (adaptando camadas já existentes, quando aplicável), preservando 100% do comportamento observável, e valida o resultado.

```
mba-ia-refactor-projects-skill/
├── README.md
├── docs/                       # deep dives — ver Documentação
├── code-smells-project/        # Projeto 1 — Python/Flask (E-commerce)
├── ecommerce-api-legacy/       # Projeto 2 — Node.js/Express (LMS)
├── task-manager-api/           # Projeto 3 — Python/Flask (Task Manager)
├── reports/                    # saída da Fase 2 de cada projeto
└── evidence/                   # logs (seção 3.4)
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

Node.js + Express 4.18.2 + `sqlite3` 5.1.6 (versões do `package.json` do boilerplate; hoje o lockfile resolve Express 4.22.1 e o manifesto pede `sqlite3` ^6.0.1) · LMS/e-learning · 3 arquivos, ~180 linhas, sem camadas.
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

**Catálogo de anti-patterns (17 entradas, acima do mínimo de 8):**

- **CRITICAL (5):** AP-01 SQL Injection · AP-02 Segredos hardcoded · AP-03 Hashing quebrado/falso · AP-04 Dado sensível vazado via serialização · AP-17 Ausência de autenticação/autorização em endpoint sensível.
- **HIGH (4):** AP-05 God Class · AP-06 Lógica duplicada · AP-07 Estado mutável global · AP-16 Persistência/ORM chamada direto na rota.
- **MEDIUM (4):** AP-08 N+1 · AP-09 Ausência de paginação · AP-10 Código morto/desconectado · AP-11 API deprecated.
- **LOW (4):** AP-12 Logging via print/console · AP-13 Configuração hardcoded · AP-14 Imports não usados · AP-15 Idioma/nomenclatura inconsistente.

Os 15 primeiros entraram porque apareceram, na prática, em pelo menos um dos 3 projetos durante a análise manual — nenhum é hipotético. Os dois últimos entraram depois, pelo motivo oposto: descrevem problemas reais que atravessaram auditorias inteiras justamente por não estarem catalogados. O AP-16 ficou no `task-manager-api` e passou pela auditoria original (postmortem completo em [`docs/results.md`](docs/results.md#bug-encontrado-após-a-entrega)); o AP-17 é o CRITICAL de ausência total de autenticação que atravessou **três** rodadas do `ecommerce-api-legacy` sem ser levantado, e só apareceu ao escrever os testes manuais de endpoint da rodada 4 ([`audit-project-2-part4.md`](reports/audit-project-2-part4.md)). O padrão se repetiu: o que o catálogo não nomeia, a Fase 2 não encontra.

**Playbook de refatoração (16 padrões, acima do mínimo de 8):** cada `RP-xx` traz exemplo antes/depois e nomeia o(s) `AP-xx` que resolve — o mapeamento cruzado é o que permite à Fase 3 aplicar a correção a partir da `Recommendation` do próprio relatório. O RP-16 (autenticação/autorização) é o único que muda comportamento observável e, por isso, exige confirmação explícita além do gate da Fase 2.

**Agnosticismo de tecnologia**, três decisões: (1) detecção, nunca suposição — a Fase 1 infere a stack a cada execução, nunca assume Python/Flask; (2) sinais de detecção descritos por *padrão* ("query montada por concatenação com valor do cliente"), não por sintaxe de uma linguagem; (3) playbook com exemplo antes/depois nas duas linguagens quando aplicável, e instrução explícita para aplicar "o mesmo princípio" numa stack sem exemplo. A prova concreta é a execução real nos 3 projetos deste repositório, em três stacks diferentes, sem qualquer alteração na skill entre uma execução e outra.

**Desafios e soluções:**
- **Risco de finding fabricado:** regra mais repetida em todos os arquivos — "nunca reportar um finding sem arquivo/linha real". Os 3 relatórios em `reports/` citam ranges de linha verificáveis.
- **Projeto parcialmente em camadas exigindo tratamento diferente de um monolito:** `architecture-guidelines.md` trata isso como categoria própria ("Partially-layered projects") — manter nomes de pasta existentes, só corrigir responsabilidades dentro deles.
- **Preservar comportamento mesmo corrigindo falhas de segurança:** redigir o hash de senha da resposta é, por definição, mudança de response shape — mas desejada. Documentada como exceção explícita em `architecture-guidelines.md`.
- **Tornar a Fase 3 mecânica, não ad hoc:** o mapeamento cruzado `AP-xx ↔ RP-xx` permite que a Fase 3 leia a `Recommendation` do finding confirmado e aplique o `RP-xx` citado, sem depender do agente "lembrar" a correção certa a cada execução.

## 3. Resultados

Os 5 itens exigidos pelo enunciado em [C) Resultados](docs/challenge-original.md#readmemd-deve-conter),
um por subseção, nesta ordem:

| # | Item exigido (enunciado, seção C) | Subseção |
|---|---|---|
| 1 | Resumo dos relatórios de auditoria dos 3 projetos (findings por severidade) | [3.1 Resumo das Auditorias](#31-resumo-das-auditorias) |
| 2 | Comparação antes/depois da estrutura de cada projeto | [3.2 Comparação Antes e Depois](#32-comparação-antes-e-depois) |
| 3 | Checklist de validação preenchido para cada projeto | [3.3 Checklist de Validação Preenchido](#33-checklist-de-validação-preenchido) |
| 4 | Screenshots ou logs das aplicações rodando após refatoração | [3.4 Evidências de Execução](#34-evidências-de-execução) |
| 5 | Observações sobre o comportamento em stacks diferentes | [3.5 Comportamento entre Diferentes Stacks](#35-comportamento-entre-diferentes-stacks) |

(3.6, logo depois, não é um dos 5 — é uma seção extra sobre limitações do repositório, fora do escopo obrigatório.)

### 3.1 Resumo das Auditorias

Narrativa completa em [`reports/`](reports/). Cada execução da Fase 2 gera um arquivo
novo (`audit-project-<N>-part<M>.md`) — relatórios anteriores nunca são sobrescritos,
porque são a evidência do estado "antes".

A tabela abaixo é a contagem por severidade exigida pelo enunciado, **uma linha por rodada**,
da primeira à mais recente de cada projeto. Ler a série inteira importa: a rodada 1 é a
auditoria do projeto como ele chegou, e é nela que o mínimo de 5 findings do
[critério de aceite](#critérios-de-aceite) se demonstra (12, 12 e 13 findings). As rodadas
seguintes são re-auditorias sobre um projeto já refatorado, então a contagem cai de propósito —
uma rodada com 2 ou 3 findings é sinal de que a anterior funcionou, não de auditoria fraca, e o
template proíbe inventar finding para preencher vaga. O texto logo depois da tabela resume o que
cada rodada efetivamente achou; o histórico achado por achado está em
[`docs/results.md`](docs/results.md#resultados-por-projeto).

<!-- BEGIN:audit-summary -->
| # | Projeto | Rodada | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---:|---|---:|---:|---:|---:|---:|---|
| 1 | `code-smells-project` | 1 | Python / Flask 3.1.1 | 4 | 3 | 2 | 4 | **13** | [`audit-project-1.md`](reports/audit-project-1.md) |
| | | 2 | Python / Flask 3.1.1 | 1 | 2 | 2 | 2 | **7** | [`audit-project-1-part2.md`](reports/audit-project-1-part2.md) |
| | | 3 | Python / Flask 3.1.1 | 1 | 0 | 2 | 2 | **5** | [`audit-project-1-part3.md`](reports/audit-project-1-part3.md) |
| | | 4 | Python / Flask 3.1.1 | 0 | 1 | 1 | 0 | **2** | [`audit-project-1-part4.md`](reports/audit-project-1-part4.md) |
| 2 | `ecommerce-api-legacy` | 1 | JavaScript / Node.js + Express 4.18.2 | 4 | 2 | 2 | 4 | **12** | [`audit-project-2.md`](reports/audit-project-2.md) |
| | | 2 | JavaScript / Node.js + Express 4.18.2, sqlite3 6.0.1 | 1 | 2 | 2 | 3 | **8** | [`audit-project-2-part2.md`](reports/audit-project-2-part2.md) |
| | | 3 | JavaScript / Node.js 26 + Express 4.22.1, sqlite3 6.0.1 | 1 | 5 | 5 | 5 | **16** | [`audit-project-2-part3.md`](reports/audit-project-2-part3.md) |
| | | 4 | JavaScript / Node.js 26 + Express 4.22.1, sqlite3 6.0.1 | 1 | 0 | 0 | 2 | **3** | [`audit-project-2-part4.md`](reports/audit-project-2-part4.md) |
| 3 | `task-manager-api` | 1 | Python / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 | 4 | 2 | 4 | 4 | **14** | [`audit-project-3.md`](reports/audit-project-3.md) |
| | | 2 | Python / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 | 0 | 2 | 2 | 3 | **7** | [`audit-project-3-part2.md`](reports/audit-project-3-part2.md) |
| | | 3 | Python / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 | 0 | 3 | 4 | 4 | **11** | [`audit-project-3-part3.md`](reports/audit-project-3-part3.md) |

<sub>Gerado por `scripts/sync-docs.sh` a partir de `reports/`: uma linha por rodada, da primeira à mais recente. Não edite à mão.</sub>
<!-- END:audit-summary -->

**`code-smells-project`** — rodada 1 (12 findings ⁰): 4 CRITICAL — SQL injection generalizada em
`models.py` (~20 pontos), `SECRET_KEY` hardcoded e vazada em `/health`. A Fase 3 corrigiu os 4
CRITICAL e reestruturou em MVC. Rodadas 2-3 acharam e fecharam achados menores herdados (SQL cru
ainda chegando a `cursor.execute` em `/admin/query`, paginação ausente, validação duplicada) —
rodada 3 fechou tudo (5 findings, 1 CRITICAL). A rodada 4 (tabela acima, 2 findings) é uma
re-auditoria pontual disparada por `api-tests.http`, não uma passada completa: achou e a Fase 3
já corrigiu 1 HIGH (update de pedido sem checar se afetou alguma linha) e 1 MEDIUM (parâmetro não
numérico derrubando endpoint com 500 em vez de 400).

**`ecommerce-api-legacy`** — rodada 1 (12 findings): 4 CRITICAL — classe-Deus `AppManager`,
segredos hardcoded incluindo uma chave `pk_live_` de gateway de pagamento, "hash" de senha que
era base64, número de cartão em log em texto plano. A Fase 3 corrigiu os 4 e quebrou em MVC.
Rodadas 2-3 reabriram e fecharam 14 dos 16 achados (checkout sem transação, cascade delete sem
checar erro, ausência de camada de serviço), com 2 LOW deixados abertos de propósito (contrato de
API, RP-15). A rodada 4 (tabela acima, 3 findings) achou 1 CRITICAL novo — nenhum endpoint tinha
autenticação/autorização — já corrigido nesta entrega com uma guarda por API key.

**`task-manager-api`** — rodada 1 (13 findings ⁰): 4 CRITICAL — hash de senha (MD5 sem sal) vazado
em toda resposta de API, `SECRET_KEY` hardcoded, token de login forjável
(`'fake-jwt-token-' + id`). A Fase 3 corrigiu os 4. Rodada 2 achou rotas chamando o ORM
diretamente (motivo de o catálogo ganhar o AP-16, ver [§2](#2-construção-da-skill)) e validação
duplicada. A rodada 3 (tabela acima, 11 findings, 0 CRITICAL) fechou os achados estruturais e, por
decisão explícita do usuário durante a Fase 3, implementou autenticação/autorização real
(token assinado + roles) no lugar do token forjável da rodada 1 — o único dos 3 projetos onde a
Fase 3 mudou comportamento observável por design, não por correção de bug.

⁰ Os relatórios `audit-project-1.md` e `audit-project-3.md` declaram, no próprio `## Summary`, 13 e 14 findings — um LOW a mais do que os blocos que cada um traz. Os números corretos são 12 e 13, e estão usados aqui. Os relatórios não foram editados (são a evidência congelada do estado "antes", e o gate de evidência trata relatório alterado como auditoria nova); a correção está registrada em [`reports/ERRATA.md`](reports/ERRATA.md).

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
├── internal-tests.py
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
    │   ├── requireAdminToken.js
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
│   ├── test_n_plus_one_queries.py
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
| Nº de arquivos condiz | ✓ 16 arquivos (rodada 4) | ✓ 24 arquivos (rodada 4) | ✓ 22 arquivos (rodada 3) |
| Relatório segue o template | ✓ | ✓ ¹ | ✓ |
| Finding com arquivo/linha exatos | ✓ | ✓ | ✓ |
| Ordenado CRITICAL → LOW | ✓ | ✓ | ✓ |
| Mínimo de 5 findings | ✓ 5 (rodada 3) ⁷ | ✓ 16 (rodada 3) ⁶ | ✓ 11 (rodada 3) |
| Detecção de API deprecated (se aplicável) | – n/a | – n/a | ✓ `datetime.utcnow()` ×18 (rodada 1) |
| Pausa e pede confirmação antes da Fase 3 | ✓ | ✓ | ✓ |
| Estrutura de diretórios segue MVC | ✓ | ✓ | ✓ camadas existentes ajustadas ² |
| Configuração extraída (sem hardcoded) | ✓ `config/settings.py` | ✓ `src/config/index.js` | ✓ `config/settings.py` |
| Models abstraem dados | ✓ | ✓ | ✓ com ressalva ¹⁰ |
| Views/Routes separadas | ✓ | ✓ | ✓ |
| Controllers concentram o fluxo | ✓ | ✓ controllers finos + `services/` de domínio | ✓ com ressalva `controllers/` ³ ⁹ |
| Error handling centralizado | ✓ com ressalva `middlewares/error_handler.py` ⁵ | ✓ `src/middlewares/errorHandler.js` | ✓ `middlewares/error_handler.py` ⁴ |
| Entry point claro | ✓ `app.py` | ✓ `src/server.js` (o `app.js` monta, sem efeito colateral) | ✓ `app.py` |
| Aplicação inicia sem erros | ✓ [rodada 3](evidence/logs/code-smells-project-round3-validation.txt) + [rodada 4](evidence/logs/code-smells-project-round4-validation.txt) | ✓ [rodada 3](evidence/logs/ecommerce-api-legacy-round3-validation.txt) + [rodada 4](evidence/logs/ecommerce-api-legacy-round4-validation.txt) | ✓ [estrutura](evidence/logs/task-manager-api-round3-validation.txt) + [auth](evidence/logs/task-manager-api-round4-validation.txt) ⁸ |
| Endpoints originais respondem | ✓ | ✓ `manual-tests.sh` na rodada 3 | ✓ |

**Notas.** As três células marcadas "com ressalva" (⁵, ⁹, ¹⁰) são achados da auditoria de release de 2026-09-20, ainda **não corrigidos** — estão aqui em vez de um `✓` limpo porque o checklist só vale se cada célula puder ser conferida no código como ele está hoje. Versão narrativa completa de cada nota em [`docs/results.md`](docs/results.md#checklist-de-validação-preenchido).

¹ **Relatório segue o template (`ecommerce-api-legacy`).** Os três relatórios do projeto seguem `references/audit-report-template.md`: cabeçalho em caixa, `Stack:`/`Files:`, `## Summary` por severidade, um bloco por finding com `File:`/`Description:`/`Impact:`/`Recommendation:` citando AP-xx/RP-xx, ordenação CRITICAL → LOW, total e a pergunta literal do gate. As partes 2 e 3 acrescentam a seção `## Resolved since …`, como o template manda para re-execução.

² **Estrutura MVC (`task-manager-api`).** O projeto já vinha com `models/`/`routes/`/`services/`/`utils/`, mas as rotas chamavam o ORM direto (AP-16, rodada 3). Fechado na mesma rodada e confirmado mecanicamente por `arch-check.sh` (exit 0, na versão do projeto e na genérica da skill).

³ **Controllers (`task-manager-api`).** `controllers/task_controller.py` e `controllers/user_controller.py` concentram parsing, validação e autorização, e recebem `actor` explícito em vez de ler estado global — o que manteve os 40 testes de controller originais passando quando a autorização entrou.

⁴ **Error handling (`task-manager-api`).** `middlewares/error_handler.py` registra dois handlers globais: um para `HTTPException` (preserva código e mensagem) e um catch-all que loga e devolve 500 genérico. Nenhuma rota trata exceção por conta própria.

⁵ **Ressalva — error handling do `code-smells-project`.** `middlewares/error_handler.py` registra handler só para `404` e para `Exception`, sem `HTTPException`. Como o Flask resolve handler subindo a hierarquia da exceção, um **`405 Method Not Allowed` cai no catch-all e volta como 500** — o Projeto 3 trata isso corretamente, este não. Além disso, os controllers mantêm ~30 blocos `try/except` locais, vários devolvendo `str(e)` ao cliente: o handler global existe, mas não é o único caminho de erro. Nenhuma rodada de auditoria levantou isso; `manual-tests.sh` do Projeto 1 não exercita 405.

⁶ **Mínimo de 5 findings (`ecommerce-api-legacy`).** A rodada 4 ([`audit-project-2-part4.md`](reports/audit-project-2-part4.md)) achou 3 findings (1 CRITICAL novo + 2 LOW herdados), abaixo de 5: é re-auditoria pontual, não passada completa, e o template proíbe inventar finding para preencher vaga — um projeto que resolveu 14 dos 16 achados da rodada anterior tem pouco a reportar. O mínimo é demonstrado pela rodada 3 (16 findings, 3 fases completas). A Fase 3 da rodada 4 rodou e foi validada.

⁷ **Mínimo de 5 findings (`code-smells-project`).** Mesma situação: a rodada 4 ([`audit-project-1-part4.md`](reports/audit-project-1-part4.md)) achou 1 HIGH + 1 MEDIUM, ambos já corrigidos e validados. O mínimo é demonstrado pela rodada 3 (5 findings) e pela rodada 1 (12).

⁸ **`task-manager-api` não tem rodada 4.** O trabalho de autenticação foi a Fase 3 da rodada 3; o `round4` no nome do log é anterior à convenção de numeração — ver [Como as rodadas são numeradas](docs/results.md#como-as-rodadas-são-numeradas).

⁹ **Ressalva — controllers do `task-manager-api`.** `routes/report_routes.py` (linhas 11, 16, 23, 30, 37 e 43) chama `services/report_service.py` direto, sem passar por controller: **6 dos 22 endpoints** não têm camada de controller. E `report_service.py:163-221` guarda o CRUD de Category, que é trabalho de controller + model sob um nome de "report". Passa no `arch-check.sh` porque service é alvo de delegação válido para o AP-16, mas contraria a convenção que o próprio projeto adota nas outras rotas.

¹⁰ **Ressalva — models do `task-manager-api`.** Os models são entidades SQLAlchemy com só parte da lógica de query (`models/task.py:96,116,128,143`); o resto do acesso a dados (`db.session.*`, `Task.query`) vive em `controllers/task_controller.py`, `controllers/user_controller.py` e `services/report_service.py`. A abstração existe, mas é inconsistente — não é ausência de model, é model contornado.

### 3.4 Evidências de Execução

O enunciado aceita screenshots **ou** logs como evidência ([9.4, item C](docs/challenge-original.md#94-requisitos)); esta entrega usa **logs de terminal reais**, capturados com a aplicação de pé, como evidência única — mais verificável linha a linha que uma captura de tela. São **15 arquivos** em [`evidence/logs/`](evidence/logs/); o inventário completo, arquivo por arquivo e com a rodada de cada um, está em [`docs/results.md`](docs/results.md#evidências-de-execução).

**Validação mais recente de cada projeto** — boot, `arch-check.sh`, um `curl` por finding corrigido na rodada e a suíte `manual-tests.sh` inteira:

| Projeto | Rodada | Log |
|---|---|---|
| `code-smells-project` | 4 | [`code-smells-project-round4-validation.txt`](evidence/logs/code-smells-project-round4-validation.txt) — rowcount check e guard de tipo na paginação fechados, `manual-tests.sh` sem regressão |
| `ecommerce-api-legacy` | 4 | [`ecommerce-api-legacy-round4-validation.txt`](evidence/logs/ecommerce-api-legacy-round4-validation.txt) — CRITICAL de autenticação fechado (header forjado/ausente agora 401), `npm run test:internal` 4/4 |
| `task-manager-api` | 3 | dois logs: [`…-round3-validation.txt`](evidence/logs/task-manager-api-round3-validation.txt) (estrutura MVC/AP-16) e [`…-round4-validation.txt`](evidence/logs/task-manager-api-round4-validation.txt) (autenticação/autorização, `pytest` 67/67) ⁸ |

A rodada 3 dos Projetos 1 e 2 continua registrada e vale pelo que prova — [`code-smells-project-round3-validation.txt`](evidence/logs/code-smells-project-round3-validation.txt) e [`ecommerce-api-legacy-round3-validation.txt`](evidence/logs/ecommerce-api-legacy-round3-validation.txt) (este inclui o detector do `arch-check` validado contra uma violação plantada).

**A skill rodando de ponta a ponta** tem duas capturas complementares: [`code-smells-project-skill-run-phase1-2-gate.txt`](evidence/logs/code-smells-project-skill-run-phase1-2-gate.txt) (Projeto 1, modo headless e somente leitura, parando na pergunta do gate) e [`ecommerce-api-legacy-skill-run-gate-answered.txt`](evidence/logs/ecommerce-api-legacy-skill-run-gate-answered.txt) (Projeto 2, execução interativa com o gate **respondido** e a Fase 3 executando).

Os 7 logs restantes — suítes `manual-tests.sh` isoladas, as duas formas do `arch-check.sh` lado a lado, o bloqueio do `DROP TABLE` no `/admin/query` e o log de servidor do checkout com cartão mascarado — estão catalogados um a um em [`docs/results.md`](docs/results.md#evidências-de-execução), junto com as [lacunas remanescentes](docs/results.md#lacunas-de-evidência).

⁸ Ver a nota ⁸ em [3.3](#33-checklist-de-validação-preenchido): o `task-manager-api` não tem rodada 4 — o `round4` no nome do log é anterior à convenção de numeração.

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

**Achados abertos da auditoria de release (2026-09-20).** Levantados numa revisão de coerência
do conjunto entregue, sem execução de skill. Estão registrados aqui, e não corrigidos, por
decisão de escopo — a correção de cada um exige nova rodada com relatório, Fase 3 e captura de
evidência com a aplicação de pé:

- **Projeto 1 — 405 vira 500, e error handling não é o único caminho de erro.** Ver a
  [nota ⁵ de 3.3](#33-checklist-de-validação-preenchido).
- **Projeto 3 — 6 endpoints sem controller e models contornados.** Ver as
  [notas ⁹ e ¹⁰ de 3.3](#33-checklist-de-validação-preenchido).
- **Projeto 1 sem `.env.example`, e com `SECRET_KEY` de fallback versionada.**
  `code-smells-project/config/settings.py:3` faz
  `os.environ.get("SECRET_KEY", "dev-only-change-me")`: sem a variável no ambiente, a aplicação
  sobe assinando sessões com uma chave que está no repositório. O `task-manager-api` adota a
  convenção oposta e mais segura — **recusa-se a subir** sem `SECRET_KEY` fora de
  desenvolvimento (`config/settings.py`, `.env.example` documentando a geração da chave). O
  Projeto 1 também é o único dos três sem `.env.example`, então `SECRET_KEY`, `ADMIN_TOKEN`,
  `DB_PATH`, `HOST`, `PORT` e `DEBUG` não estão documentados em lugar nenhum além do código.
  Nenhuma das 4 rodadas de auditoria registrou isso.
- **`arch-check.sh` dos projetos passa em silêncio se não achar arquivo de rota.** As versões
  na raiz dos 3 projetos saem **0** quando a busca por `routes/`/`views/` não retorna nada; a
  versão genérica empacotada na skill (`scripts/arch-check.sh`) sai **2** e é reportada como
  INCONCLUSIVE, nunca como aprovação. As duas checam a mesma regra (AP-16), mas falham de
  formas diferentes: renomear `routes/` faria os três checks de projeto passarem sem checar
  nada. A versão da skill já tem o comportamento correto e é a que deve ser portada.
- **`manual-tests.sh` do Projeto 1 não exercita o caminho feliz de admin.** As linhas 145 e 151
  mandam o header literal `X-Admin-Token: <ADMIN_TOKEN>`, um placeholder: numa execução limpa,
  só os caminhos 401/403 são provados. Os Projetos 2 e 3 parametrizam o token de verdade
  (`${ADMIN_TOKEN}` e `get_token`). O caminho feliz do `/admin/query` do Projeto 1 está provado
  em [`code-smells-project-admin-query-drop-table-blocked.txt`](evidence/logs/code-smells-project-admin-query-drop-table-blocked.txt),
  capturado à mão — não pela suíte.

## 4. Como Executar

### 4.1 Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`) — a skill deste repositório está no formato dele (`.claude/skills/refactor-arch/`). Gemini CLI e OpenAI Codex também são aceitos pelo enunciado; nesse caso, adapte o comando de invocação e o path da skill para a convenção da ferramenta escolhida — o conteúdo de `references/` permanece o mesmo.
- **code-smells-project** e **task-manager-api**: Python 3.10+ (`pip install -r requirements.txt`).
- **ecommerce-api-legacy**: Node.js 18+ (`npm install`). O `sqlite3` ^6.0.1 usado hoje traz binário pré-compilado a partir do Node 20; as validações desta entrega rodaram em Node 26.
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

**Rotas administrativas precisam de `ADMIN_TOKEN`.** Nos Projetos 1 e 2, os endpoints sensíveis são protegidos por uma guarda de API key e ficam **desabilitados (403) enquanto a variável não estiver definida no servidor** — é proposital: sem opt-in explícito do operador, a rota não abre. Para exercitá-los, suba a aplicação com `ADMIN_TOKEN` e mande o header `X-Admin-Token` na requisição:

```bash
# Projeto 1 — POST /admin/query e POST /admin/reset-db
ADMIN_TOKEN=um-token-qualquer python app.py
curl -X POST localhost:5000/admin/query -H "X-Admin-Token: um-token-qualquer" \
     -H "Content-Type: application/json" -d '{"tabela":"produtos"}'

# Projeto 2 — GET /api/admin/financial-report e DELETE /api/users/:id
ADMIN_TOKEN=um-token-qualquer npm start
curl localhost:3000/api/admin/financial-report -H "X-Admin-Token: um-token-qualquer"
```

O Projeto 2 tem `ADMIN_TOKEN` no `.env.example`; o Projeto 1 não tem `.env.example` — ver [3.6](#36-limitações-conhecidas-e-melhorias-futuras). O Projeto 3 usa outro mecanismo: login em `POST /login` e `Authorization: Bearer <token>`, com matriz de permissões no `README.md` do projeto.

`task-manager-api` precisa do `seed.py` antes do primeiro boot (senão os endpoints devolvem listas vazias) e falha ao subir sem `SECRET_KEY` no `.env` — o `.env.example` já traz `FLASK_ENV=development`, que dispensa configurar uma chave real para teste local. Detalhes completos (variáveis, seeds, exemplos de requisição) ficam no `README.md` de cada projeto.

### 4.3 Validação

```bash
# 1. estrutura: nenhuma rota toca persistência direto (AP-16)
cd <projeto> && ./arch-check.sh        # exit 0 = passou

# 2. a aplicação sobe e os endpoints originais respondem
#    (projeto 2 tem api.http; projetos 1 e 3, curl nos endpoints do README do projeto)

# 3. documentação em dia com os relatórios
scripts/sync-docs.sh --check           # exit 0 = README e docs/ refletem reports/,
                                       # e todo relatório tem evidência mais recente que ele
```

`arch-check.sh` existe em duas formas: a versão específica de cada projeto (na raiz dele)
e a versão genérica empacotada na skill (`scripts/arch-check.sh`), que detecta a stack
sozinha para projetos que ainda não têm uma. As duas checam a mesma regra (AP-16), mas **falham
de formas diferentes** quando nenhum arquivo de rota é encontrado: a genérica sai 2
(INCONCLUSIVE, nunca lido como aprovação) e a dos projetos sai 0 — ver
[3.6](#36-limitações-conhecidas-e-melhorias-futuras).

Este é o resumo consolidado dos 3 projetos — cada um detalha, no próprio `README.md`,
suas ferramentas de validação adicionais (`pytest` no `task-manager-api`,
`npm run test:internal` no `ecommerce-api-legacy`, `manual-tests.sh`/`api-tests.http` nos três).

## Critérios de Aceite

Mínimos exigidos pelo [enunciado](docs/challenge-original.md#97-critérios-de-aceite) —
obrigatórios nos 3 projetos, sem exceção. Mantido por `/sync-docs`. Cada `✓` aponta para o
relatório ou a evidência que o sustenta; célula em branco significa não verificado, não "falhou".

| Critério | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Fase 1 detecta stack corretamente | ✓ Python / Flask 3.1.1 | ✓ JavaScript / Node.js 26 + Express 4.22.1, sqlite3 6.0.1 | ✓ Python / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 |
| Fase 2 encontra ≥ 5 findings | ✓ 5 ([part3](reports/audit-project-1-part3.md)) ⁷ | ✓ 16 ([part3](reports/audit-project-2-part3.md)) ⁶ | ✓ 11 ([part3](reports/audit-project-3-part3.md)) |
| Fase 2 inclui ≥ 1 CRITICAL ou HIGH | ✓ 1 CRITICAL | ✓ 1 CRITICAL + 5 HIGH | ✓ 3 HIGH |
| Fase 3 aplicação funciona após refatoração | ✓ [log rodada 3](evidence/logs/code-smells-project-round3-validation.txt) + [log rodada 4](evidence/logs/code-smells-project-round4-validation.txt) | ✓ [log rodada 3](evidence/logs/ecommerce-api-legacy-round3-validation.txt) + [log rodada 4](evidence/logs/ecommerce-api-legacy-round4-validation.txt) | ✓ rodada 3, dois logs: [estrutura](evidence/logs/task-manager-api-round3-validation.txt) + [auth](evidence/logs/task-manager-api-round4-validation.txt) ⁸ |

A linha "Fase 1 detecta stack" sai da linha `Stack:` de cada relatório; as duas seguintes, da
tabela de [§3.1](#31-resumo-das-auditorias). "Aplicação funciona" só está marcada onde há registro
de execução real — boot mais endpoints respondendo. ⁶ `ecommerce-api-legacy` tem uma rodada 4
([`audit-project-2-part4.md`](reports/audit-project-2-part4.md), 2026-09-20) com só 3 findings
(1 CRITICAL + 2 LOW herdados) — abaixo do mínimo de 5, mas essa Fase 3 **já rodou e foi
validada**: o CRITICAL (ausência de autenticação/autorização) foi fechado com uma guarda por
API key (`X-Admin-Token`) em `GET /api/admin/financial-report` e `DELETE /api/users/:id`
([log rodada 4](evidence/logs/ecommerce-api-legacy-round4-validation.txt)). ⁷ Mesma situação em
`code-smells-project`: a rodada 4
([`audit-project-1-part4.md`](reports/audit-project-1-part4.md), 2026-09-20) achou 1 HIGH + 1
MEDIUM (mutação sem checar linha afetada; coerção de tipo sem guard virando 500), também abaixo
do mínimo de 5, e também já corrigida e validada
([log rodada 4](evidence/logs/code-smells-project-round4-validation.txt)). As duas notas existem
só para explicar por que a contagem de findings da rodada mais recente fica abaixo de 5, não para
sinalizar pendência. Detalhe de ambas em
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
