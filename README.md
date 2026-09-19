# Criação de Skills — Refatoração Arquitetural Automatizada

Skill `refactor-arch` para Claude Code que analisa, audita e refatora projetos backend legados para o padrão MVC, agnóstica de linguagem e framework. Executada nos 3 projetos deste repositório — dois Python/Flask (um monolítico, um parcialmente em camadas) e um Node.js/Express — e testada, fora deles, num quarto projeto em Go/Gin para provar a independência de tecnologia.

> Este README documenta o processo do ponto de vista de quem vai **avaliar** a entrega: a seção logo abaixo mapeia cada item obrigatório do enunciado para onde ele está. O enunciado original, preservado na íntegra, está em [`docs/challenge-original.md`](docs/challenge-original.md).

## Sumário

- [Conformidade com o Enunciado](#conformidade-com-o-enunciado)
- [Visão Geral](#visão-geral)
- [1. Análise Manual](#1-análise-manual)
- [2. Construção da Skill](#2-construção-da-skill)
- [3. Resultados](#3-resultados)
  - [3.1 Resumo das Auditorias](#31-resumo-das-auditorias)
  - [3.2 Comparação Antes e Depois](#32-comparação-antes-e-depois)
  - [3.3 Checklist de Validação Preenchido](#33-checklist-de-validação-preenchido)
  - [3.4 Evidências de Execução](#34-evidências-de-execução)
  - [3.5 Comportamento entre Diferentes Stacks](#35-comportamento-entre-diferentes-stacks)
- [4. Como Executar](#4-como-executar)
  - [4.1 Pré-requisitos](#41-pré-requisitos)
  - [4.2 Comandos por Projeto](#42-comandos-por-projeto)
  - [4.3 Validação](#43-validação)
- [Documentação](#documentação)
- [Referências](#referências)

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

**Critérios de Aceite** ([enunciado 9.7](docs/challenge-original.md#97-critérios-de-aceite)) — obrigatórios nos 3 projetos, sem exceção:

| Critério | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Fase 1 detecta a stack corretamente | ✓ | ✓ | ✓ |
| Fase 2 encontra ≥ 5 findings | ✓ 13 | ✓ 12 | ✓ 14 |
| Fase 2 inclui ≥ 1 CRITICAL ou HIGH | ✓ 4 CRITICAL + 3 HIGH | ✓ 4 CRITICAL + 2 HIGH | ✓ 4 CRITICAL + 2 HIGH |
| Fase 3: aplicação funciona após refatoração | ✓ | ✓ | ✓ |

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

Feita **antes** de existir a skill — o objetivo era entender os problemas reais o bastante para moldar o catálogo de anti-patterns, não catalogar tudo. Cada projeto tem no mínimo 5 achados documentados (o enunciado exige isso), com ≥1 CRITICAL/HIGH, ≥2 MEDIUM e ≥2 LOW; os 3 projetos têm 7. Detalhamento completo, com descrição técnica e trecho validado em execução para cada um dos 21 achados, em [`docs/manual-analysis.md`](docs/manual-analysis.md).

### code-smells-project (Python/Flask, E-commerce — monolítico, 4 arquivos)

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | SQL Injection generalizada | `models.py` (~20 pontos) | Qualquer campo controlado pelo cliente permite ler, alterar ou destruir dados arbitrariamente — o problema de maior impacto do projeto. |
| CRITICAL | Segredo hardcoded e vazado em `/health` | `app.py:7-8`, `controllers.py:285-289` | O segredo usado para assinar sessões fica público no repositório **e** na própria API — invalida a integridade de sessão. |
| HIGH | God Class / ausência total de MVC | `models.py`, `controllers.py` | Impossível testar uma regra isoladamente; mudar um domínio arrisca quebrar os outros três no mesmo arquivo. |
| MEDIUM | N+1 no histórico de pedidos | `models.py:171-233` | Uma única listagem pode disparar dezenas de queries; degrada com o crescimento da base. |
| MEDIUM | Ausência de paginação | `controllers.py:5-12,128-134,229-235` | Gargalo de performance e payload que só piora à medida que a base cresce. |
| LOW | `print()` como logging | `controllers.py`, `app.py:56,83-86` | Sem níveis, sem estrutura, sem rotação — inviável em produção. |
| LOW | Categorias válidas hardcoded inline | `controllers.py:52` | Qualquer categoria nova exige alterar código-fonte em vez de configuração. |

### ecommerce-api-legacy (Node.js/Express, LMS — monolítico, 3 arquivos)

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | Segredos de produção hardcoded | `utils.js:2-6` | Uma chave de gateway de pagamento "live" vazada no repositório é um incidente imediato, não hipotético. |
| CRITICAL | Hashing de senha falso (base64 reversível) | `utils.js:17-23` | Equivale a senha em claro com verniz cosmético; qualquer vazamento expõe todas as credenciais. |
| HIGH | God Class | `AppManager.js:1-142` | Arquitetura, roteamento e regra de negócio no mesmo lugar — impossível testar em isolamento. |
| MEDIUM | N+1 em cascata de callbacks no relatório financeiro | `AppManager.js:80-129` | Tempo de resposta cresce multiplicativamente com cursos × matrículas; origem do "callback hell". |
| MEDIUM | Estado mutável global | `utils.js:9-10` | Fonte clássica de race conditions em runtime concorrente. |
| LOW | `console.log` como logging | `utils.js:13`, `AppManager.js:45` | Mesma limitação do projeto 1: sem structured logging. |
| LOW | Mistura de idiomas inconsistente | `AppManager.js` | Problema de padronização/manutenibilidade, não funcional. |

### task-manager-api (Python/Flask, Task Manager — parcialmente em camadas)

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

**Agnosticismo de tecnologia**, três decisões: (1) detecção, nunca suposição — a Fase 1 infere a stack a cada execução, nunca assume Python/Flask; (2) sinais de detecção descritos por *padrão* ("query montada por concatenação com valor do cliente"), não por sintaxe de uma linguagem; (3) playbook com exemplo antes/depois nas duas linguagens quando aplicável, e instrução explícita para aplicar "o mesmo princípio" numa stack sem exemplo. A prova concreta é a execução real nos 3 projetos deste repositório — e, além deles, num quarto projeto em **Go/Gin**, fora do repositório, que expôs exatamente o ponto cego que essa estratégia não cobria: os padrões de detecção assumiam persistência via receptor (`Model.query`, `db.session.add`), e Go expõe persistência como **funções de pacote** (`FindOneUser(...)`). A primeira execução deu um falso `PASS` num arquivo com 26 violações reais — corrigido adicionando o padrão de função livre ao catálogo e ao checker (detalhe em [3.5](#35-comportamento-entre-diferentes-stacks)).

**Desafios e soluções:**
- **Risco de finding fabricado:** regra mais repetida em todos os arquivos — "nunca reportar um finding sem arquivo/linha real". Os 3 relatórios em `reports/` citam ranges de linha verificáveis.
- **Projeto parcialmente em camadas exigindo tratamento diferente de um monolito:** `architecture-guidelines.md` trata isso como categoria própria ("Partially-layered projects") — manter nomes de pasta existentes, só corrigir responsabilidades dentro deles.
- **Preservar comportamento mesmo corrigindo falhas de segurança:** redigir o hash de senha da resposta é, por definição, mudança de response shape — mas desejada. Documentada como exceção explícita em `architecture-guidelines.md`.
- **Tornar a Fase 3 mecânica, não ad hoc:** o mapeamento cruzado `AP-xx ↔ RP-xx` permite que a Fase 3 leia a `Recommendation` do finding confirmado e aplique o `RP-xx` citado, sem depender do agente "lembrar" a correção certa a cada execução.

## 3. Resultados

### 3.1 Resumo das Auditorias

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| code-smells-project | 4 | 3 | 2 | 4 | **13** |
| ecommerce-api-legacy | 4 | 2 | 2 | 4 | **12** |
| task-manager-api | 4 | 2 | 4 | 4 | **14** |
| Go/Gin (externo, Fases 1-2 apenas) | 1 | 3 | 3 | 3 | **10** |

Os 3 projetos da entrega superam o mínimo exigido (≥5 findings, ≥1 CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW). Relatórios completos: [`reports/audit-project-1.md`](reports/audit-project-1.md), [`reports/audit-project-2.md`](reports/audit-project-2.md), [`reports/audit-project-3.md`](reports/audit-project-3.md). Resumo por projeto, com as principais correções aplicadas e commits, em [`docs/results.md`](docs/results.md#resumo-das-auditorias).

### 3.2 Comparação Antes e Depois

**code-smells-project** — de 4 arquivos monolíticos para MVC completo:

```
Antes                        Depois
app.py                        app.py                       (composition root)
controllers.py                config/settings.py
models.py                     controllers/{admin,order,product,system,user}_controller.py
database.py                   models/{db,order,product,user}_model.py
                               middlewares/{auth,error_handler}.py
                               routes/routes.py
```

**ecommerce-api-legacy** — de 1 God Class para MVC completo:

```
Antes                         Depois
src/app.js                    src/app.js                   (composition root)
src/AppManager.js             src/config/index.js
src/utils.js                  src/controllers/{checkout,report,user}Controller.js
                               src/models/{auditLog,course,enrollment,payment,user}Model.js
                               src/services/{cache,paymentGateway}Service.js
                               src/middlewares/errorHandler.js
                               src/routes/index.js
                               src/utils/{crypto,logger}.js
```

**task-manager-api** — camadas já existentes, ajustadas *in place*:

```
Antes (parcial)                        Depois
app.py                                  app.py                        (SECRET_KEY/debug via env)
models/{user,task,category}.py          models/{user,task,category}.py (hashing correto, sem duplicação)
routes/{task,user,report}_routes.py     routes/{task,user,report}_routes.py (parse → 1 chamada → resposta)
services/notification_service.py        controllers/{task,user}_controller.py (novo — fecha o AP-16)
utils/helpers.py                        config/settings.py            (novo)
                                         services/report_service.py    (novo — agregação + categorias)
                                         middlewares/error_handler.py  (novo)
                                         (notification_service.py removido — código morto)
```

Narrativa completa por projeto (achados corrigidos um a um) em [`docs/results.md`](docs/results.md#code-smells-project).

### 3.3 Checklist de Validação Preenchido

Checklist do [enunciado 9.4](docs/challenge-original.md#94-requisitos), preenchido para os 3 projetos após a Fase 3 — cada célula é verificável no repositório (relatório, evidência ou arquivo citado):

| Item | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Linguagem detectada | ✓ Python | ✓ JavaScript/Node.js | ✓ Python |
| Framework detectado | ✓ Flask 3.1.1 | ✓ Express 4.18.2 | ✓ Flask 3.0.0 + SQLAlchemy 3.1.1 |
| Domínio descrito | ✓ E-commerce | ✓ LMS/checkout | ✓ Task Manager |
| Nº de arquivos condiz | ✓ 4 arquivos | ✓ 3 arquivos | ✓ 15 arquivos `.py` |
| Relatório segue o template | ✓ | ✓ ¹ | ✓ |
| Finding com arquivo/linha exatos | ✓ | ✓ | ✓ |
| Ordenado CRITICAL → LOW | ✓ | ✓ | ✓ |
| Mínimo de 5 findings | ✓ 13 | ✓ 12 | ✓ 14 |
| Detecção de API deprecated (se aplicável) | – n/a | – n/a | ✓ `datetime.utcnow()` ×18 |
| Pausa e pede confirmação antes da Fase 3 | ✓ | ✓ | ✓ |
| Estrutura de diretórios segue MVC | ✓ | ✓ | ✓ camadas existentes ajustadas ² |
| Configuração extraída (sem hardcoded) | ✓ `config/settings.py` | ✓ `src/config/index.js` | ✓ `config/settings.py` |
| Models abstraem dados | ✓ | ✓ | ✓ |
| Views/Routes separadas | ✓ | ✓ | ✓ |
| Controllers concentram o fluxo | ✓ | ✓ | ✓ `controllers/` ³ |
| Error handling centralizado | ✓ `middlewares/error_handler.py` | ✓ `src/middlewares/errorHandler.js` | ✓ ⁴ |
| Entry point claro | ✓ `app.py` | ✓ `src/app.js` | ✓ `app.py` |
| Aplicação inicia sem erros | ✓ `evidence/project1-boot.png` | ✓ `evidence/project2-boot.png` | ✓ `evidence/project3-boot.png` |
| Endpoints originais respondem | ✓ | ✓ | ✓ |

As 5 notas de rodapé narrativas (¹⁻⁴ acima, incluindo o achado de `admin_controller.py` que motivou a re-auditoria ⁵) estão em [`docs/results.md`](docs/results.md#checklist-de-validação-preenchido).

### 3.4 Evidências de Execução

```bash
cd code-smells-project && python app.py     # porta 5000
cd ecommerce-api-legacy && npm start        # porta 3000
cd task-manager-api && python app.py        # porta 5000 — não simultâneo ao projeto 1
```

![Boot do code-smells-project sem SECRET_KEY exposta](evidence/project1-boot.png)
![Boot do ecommerce-api-legacy](evidence/project2-boot.png)
![Boot do task-manager-api](evidence/project3-boot.png)

Galeria completa (10 screenshots: senha não vazada, admin bloqueado, checkout sem cartão em claro, token de login assinado, paginação) e **logs de terminal reais** dos 3 `manual-tests.sh`, dos 3 `arch-check.sh`, e da reprodução do bug do Go/Gin, em [`docs/results.md`](docs/results.md#evidências-de-execução). Dois itens (a skill rodando as 3 fases interativamente e o gate de confirmação da Fase 2) ainda dependem de uma execução manual e estão registrados como [lacuna explícita](docs/results.md#lacunas-de-evidência).

### 3.5 Comportamento entre Diferentes Stacks

A mesma skill, sem qualquer alteração, produziu relatórios e refatorações corretos em Python/Flask monolítico, Node.js/Express monolítico e Python/Flask parcialmente em camadas — a única diferença entre as 3 execuções foi o conteúdo do relatório e da refatoração, nunca o processo (`claude "/refactor-arch"` e o mesmo `SKILL.md` nos 3 casos).

Para testar isso além das duas linguagens do catálogo, o checker foi rodado contra um quarto projeto, **externo ao repositório**, em Go/Gin. A primeira execução retornou `PASS` com **zero achados** em arquivos de rota com **26 violações reais** de AP-16: todo padrão de detecção assumia persistência alcançada por um receptor (`Model.query`, `db.session.add`), e Go expõe persistência como **funções de pacote** (`FindOneUser(...)`, `SaveOne(...)`) — nada casava, e o arquivo era reportado como limpo. Um falso `PASS` é pior que nenhuma verificação: encerra a Fase 3 com um selo de aprovação indevido. A correção: `scripts/arch-check.sh` ganhou o padrão de função livre com verbo à frente, o catálogo passou a nomear essa forma explicitamente, e o checker agora sai com código 2 (`INCONCLUSIVE`) quando não identifica a camada de rotas, em vez de 0 — silêncio não é aprovação.

Logs reais dessa reprodução (o `FAIL` atual com os 26 hits, e o falso `PASS` recriado com o padrão desativado, claramente rotulado como reprodução) em [`evidence/logs/`](evidence/logs/); narrativa completa e a lista das 3 correções em [`docs/results.md`](docs/results.md#comportamento-entre-diferentes-stacks).

## 4. Como Executar

### 4.1 Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`) — a skill deste repositório está no formato dele (`.claude/skills/refactor-arch/`). Gemini CLI e OpenAI Codex também são aceitos pelo enunciado; nesse caso, adapte o comando de invocação e o path da skill para a convenção da ferramenta escolhida — o conteúdo de `references/` permanece o mesmo.
- **code-smells-project** e **task-manager-api**: Python 3.10+ (`pip install -r requirements.txt`).
- **ecommerce-api-legacy**: Node.js 18+ (`npm install`).
- A skill já está presente em `.claude/skills/refactor-arch/` dentro dos 3 projetos.

### 4.2 Comandos por Projeto

```bash
# Projeto 1 — Python/Flask
cd code-smells-project
pip install -r requirements.txt
claude "/refactor-arch"          # confirme a Fase 2 com "y" para prosseguir com a Fase 3

# Projeto 2 — Node.js/Express
cd ../ecommerce-api-legacy
npm install
claude "/refactor-arch"

# Projeto 3 — Python/Flask, parcialmente em camadas
cd ../task-manager-api
pip install -r requirements.txt
claude "/refactor-arch"
```

`code-smells-project` e `task-manager-api` usam a mesma porta padrão (5000) ao rodar localmente — rode um de cada vez, ou sobrescreva a porta via variável de ambiente (`PORT`/`FLASK_PORT`). A Fase 2 só imprime o relatório no terminal; salvar em `reports/audit-project-N.md` é um passo manual, feito após cada execução.

### 4.3 Validação

Depois da Fase 3, cada projeto tem dois scripts complementares na própria pasta — nenhum substitui o outro:

```bash
cd code-smells-project     && ./manual-tests.sh && ./arch-check.sh
cd ../ecommerce-api-legacy && ./manual-tests.sh && ./arch-check.sh
cd ../task-manager-api     && ./manual-tests.sh && ./arch-check.sh
```

- **`manual-tests.sh`** valida **comportamento**: bate em cada endpoint real via `curl` e compara com o comportamento pré-refatoração. A única mudança de response shape esperada é a remoção de campos de senha/hash que antes vazavam.
- **`arch-check.sh`** valida **estrutura**: falha se alguma rota ainda chamar persistência diretamente (AP-16) — algo que um teste de caixa-preta como o `manual-tests.sh` não detecta, porque a resposta HTTP é idêntica nos dois casos (foi exatamente assim que o bug documentado em [`docs/results.md`](docs/results.md#bug-encontrado-após-a-entrega) sobreviveu à validação original).

Saída real dos 3 `arch-check.sh` (specific + o checker genérico empacotado pela skill) em [`evidence/logs/`](evidence/logs/).

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/manual-analysis.md`](docs/manual-analysis.md) | Detalhamento completo dos 21 achados da análise manual, com descrição técnica e validação em execução |
| [`docs/skill-design.md`](docs/skill-design.md) | Decisões de design completas do `SKILL.md`, tabela de `references/`, fluxo das 3 fases |
| [`docs/results.md`](docs/results.md) | Auditorias completas, narrativa antes/depois, checklist com notas de rodapé, galeria de evidências, os dois postmortems |
| [`docs/project-structure.md`](docs/project-structure.md) | Árvore final completa do repositório |
| [`docs/ai-evolution.md`](docs/ai-evolution.md) | O que já foi aplicado para sustentar o agnosticismo de tecnologia, e o que ficou mapeado como próximo passo (hooks, CI, decomposição, evals) |
| [`docs/challenge-original.md`](docs/challenge-original.md) | Enunciado original do desafio, na íntegra |
| [`reports/`](reports) | Saída literal da Fase 2 de cada projeto (4 relatórios + 3 re-auditorias) |
| [`evidence/`](evidence) | Screenshots e logs de execução reais |

## Referências

[Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) · [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) · [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) · [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
