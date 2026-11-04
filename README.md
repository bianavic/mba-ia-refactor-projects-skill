# Refatoração Arquitetural Automatizada — `refactor-arch`

> Enunciado original preservado em [`docs/original-challenge.md`](docs/original-challenge.md).

## Sumário

1. [Análise Manual](#1-análise-manual)
2. [Construção da Skill](#2-construção-da-skill)
3. [Resultados](#3-resultados)
4. [Como Executar](#4-como-executar)

## 1. Análise Manual

Os três projetos foram lidos à mão antes de a skill existir: 8 achados no primeiro e 9 em cada um dos
outros (o enunciado pede no mínimo 5, com ao menos 1 CRITICAL ou HIGH, 2 MEDIUM e 2 LOW). As linhas se referem ao código original
do boilerplate, antes da Fase 3. As severidades seguem a escala da seção
[Definição de Severidades](docs/original-challenge.md#definição-de-severidades) do enunciado, a fonte
da verdade desta análise. Descrição, impacto e critério de severidade de cada achado estão em
[`docs/manual-analysis.md`](docs/manual-analysis.md). Dois achados do `task-manager-api` também foram
confirmados com a aplicação rodando: o hash MD5 e o serviço de notificação nunca usado.

### 1.1 `code-smells-project` — Python/Flask, e-commerce

4 arquivos, ~780 linhas, camadas separadas só por arquivo (sem pastas de camada) · CRITICAL 4 · HIGH 0 · MEDIUM 2 · LOW 2

| Severidade | Achado | Local | Por que importa |
|---|---|---|---|
| CRITICAL | SQL Injection generalizada | `models.py` (ex.: `:47-50`, `:109-111`, `:289-299`) | Campos do cliente (nome, descrição, categoria, e-mail, senha, ids do pedido, busca) são concatenados no SQL: sem autenticação, dá para entrar sem senha, ler qualquer tabela, alterar todos os produtos e criar uma conta admin. |
| CRITICAL | `SECRET_KEY` hardcoded e devolvida em `/health` | `app.py:7-8,88`, `controllers.py:285-289` | O segredo que assina sessões está no repositório e no corpo de uma resposta pública; `DEBUG=True` fixo. |
| CRITICAL | Senha em texto plano, devolvida nas respostas | `database.py:31,75-83`, `models.py:83,99,105-111,122-128` | Gravada como digitada, comparada em claro no SQL e incluída no JSON de `GET /usuarios`: uma chamada entrega a credencial de todas as contas. |
| CRITICAL | God Class / sem separação MVC | `models.py`, `controllers.py:208-210,268-274`, `app.py:51-54,69` | A separação por arquivo é só nominal: `app.py`, que registra as rotas, executa SQL; os controllers também executam SQL e misturam parsing, validação e notificação; e os 4 domínios vivem juntos em `models.py`. Banco e roteamento no mesmo arquivo violam completamente a separação de responsabilidades (critério CRITICAL do enunciado), e nada é testável isoladamente. |
| MEDIUM | N+1 no histórico de pedidos | `models.py:171-233` | Um cursor por pedido e outro por item, em loops aninhados: uma listagem dispara dezenas de queries. |
| MEDIUM | Listagens sem paginação | `controllers.py:5-12,128-134,229-235` | `/produtos`, `/usuarios` e `/pedidos` devolvem a tabela inteira. |
| LOW | `print()` como log | `controllers.py:8,11,57,61,106,161,179,182,208-210,219,248,250`, `app.py:56,83-86` | Saída solta, sem nível nem formato padrão: ruído para quem lê, sem impacto no comportamento da API. |
| LOW | Categorias válidas hardcoded | `controllers.py:52` | Uma categoria nova exige mudar o código. |

### 1.2 `ecommerce-api-legacy` — Node.js/Express, LMS com checkout

3 arquivos, ~180 linhas, sem separação de camadas · CRITICAL 4 · HIGH 1 · MEDIUM 2 · LOW 2

| Severidade | Achado | Local | Por que importa |
|---|---|---|---|
| CRITICAL | Segredos de produção hardcoded | `src/utils.js:2-5` | Usuário e senha do banco e a chave `pk_live_…` do gateway estão no código; a chave ainda vai para o log a cada checkout (`src/AppManager.js:45`). |
| CRITICAL | Hash de senha falso | `src/utils.js:17-23`, usado em `src/AppManager.js:68` | `badCrypto` devolve os 2 primeiros caracteres do base64 da senha repetidos: senhas que começam igual têm o mesmo "hash", e quem lê a tabela recupera o começo da senha decodificando o base64. |
| CRITICAL | Número completo do cartão no log | `src/AppManager.js:33,45` | Cada checkout imprime o cartão inteiro, sem máscara, junto com a chave do gateway: dado PCI-DSS em todo destino de log. |
| CRITICAL | God Class | `src/AppManager.js:4-139` | Schema, seed, rotas e regra de pagamento na mesma classe, sem camada intermediária: é o exemplo de CRITICAL do enunciado. |
| HIGH | Estado global mutável | `src/utils.js:9-10,14`, `src/AppManager.js:2` | `globalCache` acumula uma entrada por usuário, compartilhada por todas as requisições, sem limite nem expiração; `totalRevenue` é exportado por valor e nunca é atualizado. |
| MEDIUM | N+1 em cascata no relatório financeiro | `src/AppManager.js:80-129` | Uma query por curso, e por matrícula uma de usuário e outra de pagamento, aninhadas em callbacks. |
| MEDIUM | Relatório financeiro sem paginação | `src/AppManager.js:80-129` | Todos os cursos e todas as matrículas numa resposta; o payload cresce com cursos × matrículas. |
| LOW | `console.log` como log | `src/utils.js:13`, `src/AppManager.js:45` | Saída solta, sem nível nem formato padrão. O vazamento da linha `:45` é tratado no achado CRITICAL do cartão. |
| LOW | Idiomas misturados | `src/AppManager.js` | Mensagens em pt-BR e identificadores em inglês, sem convenção. |

### 1.3 `task-manager-api` — Python/Flask, gerenciador de tarefas

15 arquivos, ~1160 linhas, já com `models/`, `routes/`, `services/` e `utils/` · CRITICAL 3 · HIGH 1 · MEDIUM 3 · LOW 2

| Severidade | Achado | Local | Por que importa |
|---|---|---|---|
| CRITICAL | `SECRET_KEY` e senha SMTP hardcoded | `app.py:13`, `services/notification_service.py:7-10` | O segredo da aplicação e a credencial de e-mail estão literais no código e no histórico do git. |
| CRITICAL | Senha com MD5 sem salt | `models/user.py:27-32` | MD5 é quebrado e, sem salt, cai em rainbow table. Como a API devolve o hash (achado seguinte), recuperar a senha é trivial: os dois juntos expõem dado sensível. |
| CRITICAL | Hash de senha devolvido nas respostas | `models/user.py:16-25` (`to_dict`), servido em `routes/user_routes.py:33,85-86,129,209` | `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` entregam o hash a qualquer cliente; somado ao MD5, facilita o ataque offline. |
| HIGH | Regra de negócio `is_overdue` dentro das rotas (e duplicada) | `models/task.py:50-60`, reescrita em `routes/task_routes.py:30-39,71-80,283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43,132-136` | As pastas existem, mas a regra de domínio sai do model e vai para as rotas, reescrita 6 vezes. É HIGH pela violação de MVC (lógica de negócio presa nos controllers), não pela duplicação, que sozinha seria MEDIUM; as cópias ainda podem divergir quando alguém corrigir só uma. |
| MEDIUM | Serviço de notificação nunca usado | `services/notification_service.py` | Problema de padronização: a estrutura de camadas não corresponde ao código que roda. Parece uma funcionalidade pronta, mas nenhuma rota o importa. |
| MEDIUM | Queries N+1 nas listagens e relatórios | `routes/task_routes.py:14-51`, `routes/user_routes.py:14-22`, `routes/report_routes.py:53-56,161-163` | `GET /tasks` faz uma query de usuário e outra de categoria por task (2N+1). |
| MEDIUM | Listagens e relatórios sem paginação | `routes/task_routes.py:11-14`, `routes/user_routes.py:10-12`, `routes/report_routes.py:12-101` | Varrem a tabela inteira a cada chamada. |
| LOW | `print()` como log | `routes/task_routes.py`, `routes/user_routes.py`, `services/notification_service.py`, `utils/helpers.py:39-41` | Saída solta, sem nível nem formato padrão. |
| LOW | Imports não utilizados | `routes/task_routes.py:7` (`json, os, sys, time`), `routes/user_routes.py:6` (`hashlib, json`), `routes/report_routes.py:7-8` (`format_date, calculate_percentage, json`), `models/task.py:3` (`json`), `utils/helpers.py:3-7` (`os, json, sys, math, hashlib`), `app.py:7` (`os, sys, json`) | Ruído que esconde as dependências reais de cada arquivo. |

### 1.4 Padrões que se repetem

Apesar de stacks e níveis de organização diferentes, os três projetos convergem para os mesmos grupos de problema, o que moldou diretamente o catálogo de anti-patterns da skill:

- **Segredos e criptografia:** todos os 3 têm segredo/`SECRET_KEY` hardcoded; 2 dos 3 (`code-smells-project`, `ecommerce-api-legacy`) têm senha em texto plano ou hash quebrado/reversível, e o `task-manager-api` usa MD5 sem salt — a mesma classe de falha (catalogada depois como AP-03) em 3 implementações diferentes.
- **Vazamento de dado sensível:** `code-smells-project` e `task-manager-api` devolvem senha (plana ou hash) em respostas de endpoint (catalogado depois como AP-04); no `ecommerce-api-legacy` o dado vazado é o número completo do cartão e a chave de pagamento no log (AP-18).
- **Ausência total ou parcial de separação de camadas:** o `ecommerce-api-legacy` é monolítico (uma God Class com banco, rotas e regra numa classe só). O `code-smells-project` separa por arquivo (`app.py`, `controllers.py`, `models.py`), mas só no nome: há SQL em `app.py`, junto com as rotas, e nos controllers, e regra de domínio em `models.py`. Por isso os dois são CRITICAL. O `task-manager-api` já tem pastas `models/routes/services/utils`, mas a disciplina de responsabilidade por camada não é seguida — a regra de negócio vaza para as rotas do mesmo jeito.
- **Performance:** N+1 e ausência de paginação aparecem nos 3 projetos, sempre em endpoints de listagem/relatório.
- **Observabilidade:** os 3 usam `print()`/`console.log` como logging.

Essa repetição é o motivo pelo qual o catálogo de anti-patterns foi desenhado como uma lista de sinais de detecção agnósticos de linguagem, e não como regras específicas de Flask ou Express: o mesmo `AP-01` (SQL Injection) precisa reconhecer tanto `"...WHERE id = " + str(id)` em Python quanto template literals em JavaScript.

## 2. Construção da Skill

A skill `refactor-arch` automatiza o que a análise manual fez: detecta a stack, audita o código
contra um catálogo de anti-patterns, pede confirmação humana e refatora para MVC provando que a
aplicação continua funcionando. O código está em
[`code-smells-project/.claude/skills/refactor-arch/`](code-smells-project/.claude/skills/refactor-arch/SKILL.md),
com uma cópia em cada um dos outros dois projetos. Detalhes em [`docs/skill-construction.md`](docs/skill-construction.md).

**Estrutura.** `SKILL.md` (frontmatter, fluxo das 3 fases, regras inegociáveis) mais referências em
Markdown em `references/`, carregadas sob demanda por fase, e dois scripts em `scripts/`
(`arch-check.sh` e `completion-box.sh`):

| Área exigida | Arquivo | Conteúdo |
|---|---|---|
| Análise de projeto | `project-analysis.md` | Detecção de linguagem, framework, banco, arquitetura e inventário de endpoints |
| Catálogo de anti-patterns | `anti-patterns-catalog.md` | 23 anti-patterns pela severidade base: 7 CRITICAL, 4 HIGH, 8 MEDIUM, 4 LOW. AP-04, AP-06, AP-12, AP-18 e AP-21 têm regra própria para subir ou descer (ex.: AP-06 é CRITICAL quando um único arquivo junta banco, rotas e regra, ou quando a separação é só nominal, com o arquivo de rotas ou um controller executando SQL direto por fora da camada de dados) |
| Template de relatório | `audit-report-template.md` | Formato fixo do relatório da Fase 2 |
| Guidelines de arquitetura | `architecture-guidelines.md` | Camadas MVC e tabela de decisão de colocação |
| Playbook de refatoração | `refactoring-playbook.md` | 22 padrões antes/depois (21 em Python, 17 também em JavaScript/Node; o RP-22 mostra a árvore de pastas), um ou mais por anti-pattern |

Há ainda `refactoring-validation.md` (validação da Fase 3: `api-test.sh`, `arch-check.sh`, checagem por
finding, anti-tautologia, log de validação, evidências da caixa final). `arch-check.sh` faz a
verificação estrutural agnóstica de stack; `completion-box.sh` gera a caixa
`PHASE 3: REFACTORING COMPLETE` e só a imprime quando as pré-condições passam. As regras das
decisões abertas e o formato do plano ficam no próprio `SKILL.md`, na Fase 2.

**Catálogo e por quê.** Os 23 anti-patterns vêm de quatro fontes: os achados da análise manual (§1),
o enunciado (exemplos da escala de severidade e a exigência de detectar APIs deprecated, o AP-12), os
desafios que apareceram ao rodar a skill e problemas presentes nos projetos que a análise manual não
listou (AP-05, AP-20 e AP-23). Dos 23, 22 viraram finding em pelo menos um relatório. O AP-17 é a
exceção: ele só existe depois que há autorização para contornar, por isso aparece no relatório 1 como
uma checagem a repetir após a Fase 3.

| Severidade base | Anti-patterns | Por que entraram |
|---|---|---|
| CRITICAL (7) | AP-01 SQL injection · AP-02 segredos hardcoded · AP-03 hash de senha quebrado/ausente · AP-04 dado sensível na serialização · AP-05 falta de autenticação/autorização · AP-17 escalada de privilégio no auto-cadastro · AP-20 endpoint de execução arbitrária | AP-01 e AP-02 são os exemplos de CRITICAL do enunciado e estão na §1 (SQL concatenado no code-smells; segredos nos 3 projetos). AP-03 e AP-04 generalizam o texto plano, o `badCrypto` e o MD5 da §1 e a senha/hash devolvidos nas respostas. AP-05 cobre as rotas de admin e de dados pessoais abertas nos 3 projetos, e AP-20 o `POST /admin/query` do code-smells, que executa SQL do cliente. AP-17 veio de um desafio: a Fase 3 criou a guarda de admin, e o cadastro aceitava `role` do corpo. Todos expõem dado ou dão controle a quem não deveria tê-lo |
| HIGH (4) | AP-06 God Class · AP-07 regra de negócio duplicada · AP-08 estado global mutável · AP-22 orquestração fora de um Service | Dois exemplos de HIGH do enunciado: regra de negócio presa nas rotas/controllers (AP-22, o padrão do task-manager) e estado global mutável (AP-08, `globalCache`/`totalRevenue` do ecommerce). AP-06 aplica a definição geral de HIGH (forte violação de MVC) e sobe a CRITICAL quando a separação de responsabilidades é violada por completo: banco, regra e roteamento numa classe só (ecommerce) ou separação só nominal, com SQL cru no arquivo de rotas (code-smells, §1). Rotas que chamam o ORM, como no task-manager, ficam no AP-22. AP-07 vem da regra `is_overdue` do task-manager, reescrita em várias rotas: duplicação sozinha seria MEDIUM no enunciado, mas aqui a regra duplicada é de domínio e saiu do model, o que a torna violação de MVC. Não expõem dado, mas impedem testar e mudar uma parte sem as outras |
| MEDIUM (8) | AP-09 N+1 · AP-10 sem paginação · AP-11 camada morta/desconectada · AP-12 APIs deprecated e versões vulneráveis/EOL · AP-18 dado pessoal em log · AP-19 direitos do titular incompletos · AP-21 validação de entrada ausente · AP-23 módulos soltos na raiz | AP-09 e AP-21 são exemplos de MEDIUM do enunciado; AP-09 e AP-10 aparecem nos 3 projetos (§1.4). AP-12 atende a exigência de detectar APIs deprecated e cobre também versões fixadas com advisory. AP-11 vem do serviço de notificação que nenhuma rota usa. AP-18 e AP-19 vieram de um desafio (a lente de dado pessoal): o cartão no log do ecommerce e a falta de exclusão, exportação e retenção nos 3. AP-23 cobre `database.py` e afins na raiz, que o layout MVC precisa mover; scripts avulsos como `seed.py` podem ficar. Custam desempenho, manutenção ou conformidade, sem exposição imediata (AP-12, AP-18 e AP-21 sobem quando há) |
| LOW (4) | AP-13 `print`/`console.log` como log · AP-14 configuração/valores mágicos · AP-15 imports não usados · AP-16 nomenclatura inconsistente | Os exemplos de LOW do enunciado (nomenclatura ruim, *magic numbers*) e os LOW da §1: `print()`/`console.log` nos 3, categorias hardcoded no code-smells, imports não usados no task-manager e idiomas misturados no ecommerce. Afetam legibilidade, não comportamento |

**Decisões de design**
- **Catálogo → playbook.** Cada finding cita um `AP-xx` e um `RP-xx`; a Fase 3 aplica o padrão que o plano aprovado nomeia, em vez de improvisar. O catálogo inclui detecção de APIs deprecated e de versões fixadas vulneráveis ou EOL (AP-12).
- **Pausa obrigatória.** A Fase 2 grava o relatório, pergunta cada decisão em aberto e só segue após `y` à pergunta literal do enunciado; antes disso o único arquivo escrito é o relatório em `reports/`, e nenhum arquivo do projeto muda.
- **Prova, não declaração.** A Fase 3 só conclui com boot, `api-test.sh` exit 0, `arch-check.sh` exit 0 e artefatos em disco; cada `✓` da caixa final exige sua evidência.
- **Proteção de dados.** LGPD, GDPR e PCI-DSS orientam o `Impact` e a `Recommendation` dos findings que envolvem dado pessoal ou de cartão (quem lê o dado, por quanto tempo, o que acontece com o que já foi gravado), sem mudar a escala de severidade do enunciado.

**Como a skill se mantém agnóstica**
1. **Detecção a cada execução.** A Fase 1 infere linguagem, framework e banco dos manifests (`requirements.txt`, `package.json`, `go.mod`, `pom.xml`…) e confirma nos imports do código. A regra 1 do `SKILL.md` proíbe reaproveitar a stack de uma execução anterior.
2. **Sinais por padrão, não por sintaxe.** Cada anti-pattern descreve o padrão e cita equivalentes nas stacks cobertas; o playbook usa nomes genéricos (`<table>`, `<entity>`), traduzidos para o projeto analisado.
3. **Cobertura declarada.** Sinal de uma stack sem cobertura é relatado como lacuna, nunca como aprovação.
4. **Verificação configurável.** O `arch-check.sh` localiza rotas, models e controllers por heurística e aceita ajuste por projeto em `.arch-check.conf`, sem mudar a skill. O `code-smells-project` usa esse arquivo para reconhecer `get_db().execute(...)`.

A prova é a execução: as mesmas cópias da skill rodaram em Python/Flask e Node.js/Express, em código sem camadas e em código parcialmente organizado (§3.5). O limite também é declarado: Python/Flask e Node.js/Express são o perfil coberto e os únicos testados.

**Desafios** (tabela completa em [`docs/skill-construction.md`](docs/skill-construction.md#desafios-e-como-a-skill-os-trata)):
- **Finding fabricado:** regra de `file:line` real, reaberto e conferido, nas regras inegociáveis e no catálogo.
- **Projeto já em camadas:** a categoria *Partially-layered projects* manda manter as pastas existentes e mover só a responsabilidade errada.
- **Segurança sem quebrar o contrato:** a resposta de um endpoint só muda para corrigir um defeito e na opção que o usuário escolheu na Fase 2; o plano marca essas linhas como `[CONTRACT_CHANGE]` com a origem `you chose`, e nenhuma opção remove endpoint.
- **Fase 3 ad hoc:** mapa `AP-xx ↔ RP-xx` faz cada finding apontar para a correção a aplicar.
- **Falha que a Fase 2 não viu:** a guarda de admin era contornável por `role` no cadastro; virou o AP-17.
- **Projetos sem relatório ou evidência:** a skill passou a salvar relatório e log em disco e a tratar a ausência deles como fase incompleta.
- **Dado pessoal fora do catálogo:** criados o AP-18 (PII em log) e o AP-19 (direitos do titular) e a lente de proteção de dados no template.

## 3. Resultados

### 3.1 Findings por severidade

Números copiados da linha `## Summary` de cada relatório em `reports/`.

Como ler os relatórios:
- **São a saída da Fase 2.** Cada finding descreve o código como estava antes da refatoração, e os
  `File:` apontam para as linhas do código original do boilerplate. Vários desses arquivos não
  existem mais na árvore atual (ex.: `code-smells-project/models.py`); para conferir uma linha,
  abra o mesmo caminho no [repositório base do desafio](https://github.com/devfullcycle/mba-ia-refactor-projects-skill).
- **Os relatórios não foram regravados depois da Fase 3.** O que cada finding virou está no log de
  validação, em `## Future improvements` do README de cada projeto (§3.6) e em
  [`docs/results-deep-dive.md`](docs/results-deep-dive.md). Uma nova execução da Fase 2 re-auditaria o
  projeto inteiro: removeria os findings corrigidos, manteria sem alteração os abertos (inclusive os
  corrigidos só em parte) e inseriria os novos na posição da severidade, pela regra de re-execução do
  template
  ([`audit-report-template.md`](code-smells-project/.claude/skills/refactor-arch/references/audit-report-template.md#re-runs)).

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---:|---:|---:|---:|---:|---|
| `code-smells-project` | Python 3.11.15 + Flask 3.1.1 | 8 | 3 | 7 | 4 | 22 | [audit-project-1.md](reports/audit-project-1.md) |
| `ecommerce-api-legacy` | JavaScript (Node.js 26.13.0) + Express 4.22.1 | 7 | 3 | 5 | 4 | 19 | [audit-project-2.md](reports/audit-project-2.md) |
| `task-manager-api` | Python 3.11.15 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, SQLite) | 7 | 3 | 8 | 4 | 22 | [audit-project-3.md](reports/audit-project-3.md) |

Total recontado pelos blocos `### [SEVERIDADE]` de cada relatório; bate com a linha `## Summary` e
com o rodapé `Total: <N> findings`.

### 3.2 Estrutura antes/depois

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
├── code-smells-project-api-curls.http
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
├── ecommerce-api-legacy-api-curls.http
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
├── task-manager-api-api-curls.http
└── utils/
    ├── __init__.py
    ├── helpers.py
    ├── pagination.py
    └── security.py
```

</td></tr></table>

<!-- END:project-trees -->

### 3.3 Checklist de Validação

Checklist do enunciado ([`docs/original-challenge.md`](docs/original-challenge.md)).

| Fase | Item | `code-smells-project` | `ecommerce-api-legacy` | `task-manager-api` |
|---|---|---|---|---|
| 1 — Análise | Linguagem detectada corretamente | ✓ Python 3.11.15 | ✓ JavaScript (Node.js 26.13.0) | ✓ Python 3.11.15 |
| 1 — Análise | Framework detectado corretamente | ✓ Flask 3.1.1 | ✓ Express 4.22.1 | ✓ Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 |
| 1 — Análise | Domínio da aplicação descrito corretamente | ✓ E-commerce API (produtos, usuarios, pedidos, relatorios de vendas) | ✓ LMS / course checkout API (checkout, courses, enrollments, payments, users, financial report) | ✓ Task management API (tasks, users, categories, reports) |
| 1 — Análise | Número de arquivos analisados condiz com a realidade | ✓ 4 arquivos, ~780 linhas (original: 4 `.py`, 780 linhas) | ✓ 3 arquivos, ~180 linhas (original: 3 `.js`, 180 linhas) | ✓ 15 arquivos, ~1160 linhas (original: 15 `.py`, 1158 linhas) |
| 2 — Auditoria | Relatório segue o template | ✓ cabeçalho, `## Summary`, 22/22 findings com `File`/`Description`/`Impact`/`Recommendation`, `Total:` | ✓ cabeçalho, `## Summary`, 19/19 findings com os 4 campos, `Total:` | ✓ cabeçalho, `## Summary`, 22/22 findings com os 4 campos, `Total:` |
| 2 — Auditoria | Cada finding tem arquivo e linhas exatos | ✓ 22/22 `File:` com `arquivo:linha` | ✓ 19/19 `File:` com `arquivo:linha` | ✓ 22/22 `File:` com `arquivo:linha` |
| 2 — Auditoria | Findings ordenados por severidade | ✓ CRITICAL → LOW | ✓ CRITICAL → LOW | ✓ CRITICAL → LOW |
| 2 — Auditoria | Mínimo de 5 findings | ✓ 22 | ✓ 19 | ✓ 22 |
| 2 — Auditoria | Detecção de APIs deprecated (se aplicável) | ✓ finding AP-12 (MEDIUM: Flask 3.1.1, flask-cors 5.0.1, Python 3.11.15); após a Fase 3, `clean`: python 3.11.18, flask 3.1.3, flask-cors 6.0.5, werkzeug 3.1.9, itsdangerous 2.2.0, sqlite3 stdlib | ✓ findings AP-12 (CRITICAL express 4.22.1, MEDIUM sqlite3 5.1.7); após a Fase 3, `clean`: node 26.13.0, express 4.22.3, sqlite3 6.0.1 (sem manutenção, risco aceito) | ✓ findings AP-12 (CRITICAL: flask-cors 4.0.0; MEDIUM: Flask 3.0.0/Python 3.11.15/pins sem uso; MEDIUM: `Query.get()` deprecated); após a Fase 3, `clean`: python 3.11.18, flask 3.1.3, flask-cors 6.0.5, sqlalchemy 2.1.6 (`Query.get` ×16 → 0), python-dotenv 1.2.2; marshmallow e requests removidos |
| 2 — Auditoria | Skill pausa e pede confirmação antes da Fase 3 | ✓ `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` | ✓ mesma linha | ✓ mesma linha |
| 3 — Refatoração | Estrutura de diretórios segue padrão MVC | ✓ `routes/` → `controllers/` → `services/` → `models/` | ✓ `src/routes/` → `src/controllers/` → `src/services/` → `src/models/` | ✓ `routes/` → `controllers/` → `services/` → `models/` |
| 3 — Refatoração | Configuração extraída para módulo de config | ✓ `config/settings.py` (único leitor do ambiente; `.env.example`) | ✓ `src/config/index.js` (único leitor do ambiente; `.env.example`) | ✓ `config/settings.py` (único leitor do ambiente; `.env.example`) |
| 3 — Refatoração | Models criados para abstrair dados | ✓ `models/`: pedido, produto, usuario | ✓ `src/models/`: auditLog, course, enrollment, payment, user | ✓ `models/`: category, task, user |
| 3 — Refatoração | Views/Routes separadas | ✓ `routes/`: 6 módulos (blueprints) | ✓ `src/routes/`: 3 routers | ✓ `routes/`: 5 módulos (blueprints) |
| 3 — Refatoração | Controllers concentram o fluxo | ✓ `controllers/`: 6; `arch-check.sh` PASS | ✓ `src/controllers/`: 3; `arch-check.sh` PASS | ✓ `controllers/`: 6; `arch-check.sh` PASS |
| 3 — Refatoração | Error handling centralizado | ✓ `errors/handlers.py` (`AppError` + `Exception`), registrado em `app.py` | ✓ `src/errors/errorHandler.js`, último middleware de `src/app.js` | ✓ `errors/handlers.py` (`AppError` + `Exception`), registrado em `app.py` |
| 3 — Refatoração | Entry point claro | ✓ `app.py` (raiz de composição) | ✓ `src/app.js` (raiz de composição; `npm start`) | ✓ `app.py` (raiz de composição) + `seed.py` |
| 3 — Refatoração | Aplicação inicia sem erros | ✓ boot no log, `GET /health` 200 | ✓ boot no log, escutando na porta 3000 | ✓ seed + boot no log, `GET /health` 200 |
| 3 — Refatoração | Endpoints originais respondem corretamente | ✓ 173 checks, 0 falhas; 19 originais + 2 novos (21/21) | ✓ 100 checks, 0 falhas; 3 originais + 1 novo (4/4) | ✓ 217 checks, 0 falhas; 22 originais, nenhum novo (22/22) |

**Endpoints novos e mudanças de contrato.** Todos os métodos e caminhos originais continuam existindo.
Os novos são `DELETE /usuarios/<id>` e `GET /usuarios/<id>/export` no `code-smells-project` e
`GET /api/users/:id/export` no `ecommerce-api-legacy`. "Respondem corretamente" inclui as mudanças
escolhidas na Fase 2: rotas antes abertas agora devolvem 401 ou 403 sem a credencial exigida, as
respostas não trazem mais senha, hash nem segredos, e `POST /admin/query` responde 403 enquanto
`ADMIN_QUERY_ENABLED` estiver desligado. O acesso de cada rota está no inventário do cabeçalho de cada
`api-test.sh`.

Fontes por coluna (as mesmas nos três projetos):
- Linguagem, framework, arquivos, template, `File:`, ordem, total e pausa: o relatório do projeto
  ([1](reports/audit-project-1.md), [2](reports/audit-project-2.md), [3](reports/audit-project-3.md)) —
  cabeçalho, blocos `### [SEVERIDADE]` e última linha. A contagem "original" de arquivos e linhas é a
  dos arquivos-fonte da versão original do boilerplate.
- Domínio e APIs deprecated: linhas `Domain:` e `AP-12:` do log de validação
  ([1](evidence/logs/code-smells-project-validation.txt), [2](evidence/logs/ecommerce-api-legacy-validation.txt),
  [3](evidence/logs/task-manager-api-validation.txt)) e os findings AP-12 do relatório.
- Itens da Fase 3: a árvore "depois" da §3.2, o código do projeto (`app.py`/`src/app.js`, `config/`,
  `errors/`) e a saída de `arch-check.sh <projeto>` (exit 0 nos três).
- Inicia / endpoints respondem: seções `## Boot` e rodapé do `api-test.sh` no log de validação.

### 3.4 Evidências

| Projeto | Log de validação | Checks | Falhas | Pulados | Cobertura | Exit `api-test.sh` | Exit `arch-check.sh` |
|---|---|---:|---:|---:|---|---:|---:|
| `code-smells-project` | [log](evidence/logs/code-smells-project-validation.txt) | 173 | 0 | 0 | 21/21 | 0 | 0 |
| `ecommerce-api-legacy` | [log](evidence/logs/ecommerce-api-legacy-validation.txt) | 100 | 0 | 0 | 4/4 | 0 | 0 |
| `task-manager-api` | [log](evidence/logs/task-manager-api-validation.txt) | 217 | 0 | 0 | 22/22 | 0 | 0 |

Checks, falhas, pulados, cobertura e exit do `api-test.sh` vêm do rodapé de cada log. O exit do
`arch-check.sh` não fica no log: é o de `<projeto>/.claude/skills/refactor-arch/scripts/arch-check.sh <projeto>`
na árvore atual (PASS nos três) — o mesmo portão que o `completion-box.sh` exige para emitir a caixa abaixo.

Trechos dos logs, com boot e rodapé (sem data e hora). As portas 5050 e 5070 vêm do `APP_PORT` usado na validação:

```text
# code-smells-project
INFO __main__: SERVIDOR INICIADO em http://127.0.0.1:5050
INFO werkzeug: 127.0.0.1 - - "GET /health HTTP/1.1" 200 -
TOTAL: 173 checks | failures: 0 | skipped: 0
Coverage: 21 endpoints inventoried / 21 exercised
api-test.sh exit code: 0

# ecommerce-api-legacy
[INFO] Frankenstein LMS rodando na porta 3000...
[harness] application listening on port 3000 — preflight answered HTTP 401
TOTAL: 100 checks | failures: 0 | skipped: 0
Coverage: 4 endpoints inventoried / 4 exercised
api-test.sh exit code: 0

# task-manager-api
Seed concluído com sucesso!
 * Running on http://127.0.0.1:5070
INFO werkzeug: 127.0.0.1 - - "GET /health HTTP/1.1" 200 -
TOTAL: 217 checks | failures: 0 | skipped: 0
Coverage: 22 endpoints inventoried / 22 exercised
api-test.sh exit code: 0
```

#### Caixa de conclusão da Fase 3

O `✓ Zero anti-patterns remaining` vem do template do enunciado e significa que cada finding foi resolvido ou deixado em aberto por decisão na Fase 2. Os itens em aberto estão na [§3.6](#36-achados-em-aberto-e-melhorias-futuras).

<!-- BEGIN:completion-box -->
Saída literal do `completion-box.sh` de cada projeto, na seção "Conclusão da Fase 3" do README dele:

- [`code-smells-project`](code-smells-project/README.md#conclusão-da-fase-3)
- [`ecommerce-api-legacy`](ecommerce-api-legacy/README.md#conclusão-da-fase-3)
- [`task-manager-api`](task-manager-api/README.md#conclusão-da-fase-3)

<!-- END:completion-box -->

### 3.5 Comportamento entre diferentes stacks

A mesma skill, sem nenhuma alteração entre projetos, rodou em dois
ecossistemas e em três níveis de organização.

| | `code-smells-project` | `ecommerce-api-legacy` | `task-manager-api` |
|---|---|---|---|
| Stack detectada | Python 3.11.15 + Flask 3.1.1 ([relatório](reports/audit-project-1.md)) | JavaScript (Node.js 26.13.0) + Express 4.22.1 ([relatório](reports/audit-project-2.md)) | Python 3.11.15 + Flask 3.0.0 ([relatório](reports/audit-project-3.md)) |
| Organização do boilerplate | 4 arquivos `.py` soltos na raiz | 3 arquivos `.js`; `AppManager.js` concentra rotas, regras e SQL | 15 arquivos já separados em `models/`, `routes/`, `services/` e `utils/`, sem `controllers/` |
| Diagnóstico de camadas (AP-06) | CRITICAL: SQL no código de rotas, com separação só nominal | CRITICAL: God Class; `arch-check.sh` reportou `controllers:0` e `models:0` | HIGH: rotas com persistência e regra de negócio (76 chamadas de persistência) |
| Camadas depois da Fase 3 (§3.2) | `routes/` 6, `controllers/` 6, `services/` 4, `models/` 3 | `src/routes/` 3, `controllers/` 3, `services/` 4, `models/` 5 | `routes/` 5, `controllers/` 6, `services/` 4, `models/` 3 |
| Versões vulneráveis (AP-12) | Python 3.11.15, Flask 3.1.1 e flask-cors 5.0.1 → `clean` | Express 4.22.1 (CRITICAL) e sqlite3 5.1.7 (MEDIUM) → `clean` | flask-cors 4.0.0 (CRITICAL), Flask 3.0.0 e pins sem uso (MEDIUM) → `clean` |

**Observações**

- **Mesma skill, resultados diferentes.** As três cópias de `.claude/skills/refactor-arch/` são idênticas (conferido com `diff -rq`). As diferenças nos achados vêm do código de cada projeto, não de configuração por stack.
- **Auditoria de dependências por ecossistema.** Em Python, o AP-12 usou `pip-audit` e api.osv.dev; em Node, `npm audit` (linhas `AP-12:` de cada log de validação). A checagem de versões depende da ferramenta do ecossistema.
- **O verificador estrutural não basta sozinho.** No ecommerce, `arch-check.sh` não listou `src/utils.js`: o achado de configuração e criptografia misturadas (MEDIUM, [relatório](reports/audit-project-2.md)) veio da leitura do arquivo. No `ecommerce-api-legacy`, o `arch-check.sh` também não detecta um controller escrito em uma única linha ([Future improvements](ecommerce-api-legacy/README.md#future-improvements)).
- **Camadas por diretório.** O `arch-check.sh` conta arquivos por pasta: isso prova que a estrutura existe, não que a regra foi cumprida. Por isso o AP-06 foi lido nos três projetos, e não só contado.

### 3.6 Achados em aberto e melhorias futuras

Os achados que ficaram em aberto após a Fase 3 estão na seção `## Future improvements` do README de cada projeto, cada item com a sua origem (deixado em aberto no plano, risco aceito, fora do código, notado na Fase 3 ou na revisão de segurança pós-Fase 3):

- [`code-smells-project/README.md`](code-smells-project/README.md#future-improvements)
- [`ecommerce-api-legacy/README.md`](ecommerce-api-legacy/README.md#future-improvements)
- [`task-manager-api/README.md`](task-manager-api/README.md#future-improvements)

Rodada final em detalhe — findings por severidade, o que a Fase 3 mudou e o que ficou em aberto em cada projeto:
[`docs/results-deep-dive.md`](docs/results-deep-dive.md).

### 3.7 Critérios de Aceite

| Critério | `code-smells-project` | `ecommerce-api-legacy` | `task-manager-api` |
|---|---|---|---|
| Stack detectada | ✓ Python 3.11.15 + Flask 3.1.1 | ✓ JavaScript (Node.js 26.13.0) + Express 4.22.1 | ✓ Python 3.11.15 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, SQLite) |
| ≥ 5 findings | ✓ 22 | ✓ 19 | ✓ 22 |
| ≥ 1 CRITICAL ou HIGH | ✓ 8 CRITICAL, 3 HIGH | ✓ 7 CRITICAL, 3 HIGH | ✓ 7 CRITICAL, 3 HIGH |
| Aplicação funciona após a refatoração | ✓ boot + `api-test.sh` exit 0 | ✓ boot + `api-test.sh` exit 0 | ✓ boot + `api-test.sh` exit 0 |

Stack da linha `Stack:` de cada relatório; contagens da §3.1; "funciona" do log de validação (§3.4).
Os mínimos de 2 MEDIUM e 2 LOW são da análise manual (enunciado, "Requisitos" §1), não critério de
aceite da skill. Distribuição MEDIUM/LOW de cada relatório (§3.1): `code-smells-project` 7 MEDIUM / 4 LOW,
`ecommerce-api-legacy` 5 MEDIUM / 4 LOW, `task-manager-api` 8 MEDIUM / 4 LOW.

**Análise manual × Fase 2.** O enunciado pede que a Fase 2 encontre no mínimo 5 dos problemas da
análise manual. Cada achado da §1 foi procurado no relatório do projeto:

| Projeto | Encontrados | Observação |
|---|---:|---|
| `code-smells-project` | 8 de 8 | God Class aparece como `Routing code runs raw SQL past the data layer` (AP-06); senha em texto plano e senha nas respostas viraram 2 findings; categorias hardcoded estão em `Hardcoded configuration and magic values` |
| `ecommerce-api-legacy` | 8 de 9 | Não encontrado: idiomas misturados (LOW) |
| `task-manager-api` | 9 de 9 | `is_overdue` nas rotas aparece em `Route files hold persistence and business rules` e `Overdue rule, task serialization, statistics and validation copied across handlers`; o serviço de notificação está em `Notification service, helpers and model methods implemented but never used` |

## 4. Como Executar

### 4.1 Pré-requisitos

**Ferramenta: Claude Code.** Instale pelo [setup oficial](https://code.claude.com/docs/en/setup) e
faça login com sua conta: rode `claude` uma vez e siga as instruções.

**Rede.** A Fase 2 consulta fontes externas no portão AP-12: registro de pacotes, OSV e, quando
disponíveis, `pip-audit` e `npm audit`. Sem acesso a nenhuma fonte, o componente fica `BLOCKED` e a
skill pergunta se tenta de novo ou segue com ele não verificado.

Runtime por projeto:

| Projeto | Runtime | Versão | De onde sai | Banco SQLite |
|---|---|---|---|---|
| `code-smells-project` | Python | 3.11.18 | `.python-version` (o relatório detectou 3.11.15) | `DB_PATH` (padrão `loja.db`) |
| `ecommerce-api-legacy` | Node.js e npm | 26.13.0 | versão com que o projeto foi validado; versões anteriores não foram testadas | `DB_FILE` (padrão `:memory:`) |
| `task-manager-api` | Python | 3.11.18 | `.python-version` (o relatório detectou 3.11.15) | `DATABASE_URL` (padrão `sqlite:///tasks.db`) |

Ferramentas usadas pelos scripts, conforme o próprio código:

- `api-test.sh` dos três: `bash`, `curl`, `sqlite3`, `python3` e utilitários padrão do sistema.
- `arch-check.sh`: `bash`, `awk`, `basename`, `find`, `grep`, `head`, `mktemp`, `sed`, `sort`, `tr` e `wc`.
- `completion-box.sh`: `bash`, `basename`, `dirname`, `grep`, `sed`, `sort` e `tail`.
- Os READMEs de `code-smells-project` e `ecommerce-api-legacy` usam `lsof` para encerrar a aplicação.

Particularidades por sistema operacional:

- **macOS:** é onde a validação foi rodada.
- **Linux e Windows:** não testados. Os scripts são `bash`, então no Windows é preciso WSL ou Git Bash.

### 4.2 Executar a skill (reproduzir a refatoração)

Os projetos desta árvore já estão refatorados: rodar a skill aqui reaudita o código atual e atualiza os relatórios em `reports/`. Para reproduzir a refatoração desde o início, clone o repositório base do desafio, que traz o boilerplate sem a skill, e copie a skill para os 3 projetos. Na raiz do repositório:

```bash
git clone https://github.com/devfullcycle/mba-ia-refactor-projects-skill.git ../refactor-repro
for p in code-smells-project ecommerce-api-legacy task-manager-api; do
  mkdir -p "../refactor-repro/$p/.claude/skills"
  cp -R "$p/.claude/skills/refactor-arch" "../refactor-repro/$p/.claude/skills/"
done
cd ../refactor-repro
```

Depois rode a skill a partir da pasta de cada projeto (é lá que fica a cópia em `.claude/skills/refactor-arch/`):

```bash
# Projeto 1 — Python/Flask (e-commerce)
cd code-smells-project
claude /refactor-arch

# Projeto 2 — Node.js/Express (LMS com checkout)
cd ../ecommerce-api-legacy
claude /refactor-arch

# Projeto 3 — Python/Flask (task manager)
cd ../task-manager-api
claude /refactor-arch
```

Em cada execução: a Fase 1 imprime a caixa `PHASE 1: PROJECT ANALYSIS`; a Fase 2 grava `reports/audit-project-<N>.md` na raiz do repositório, faz as perguntas das decisões em aberto, mostra o plano e para em `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para liberar a Fase 3, que termina com a caixa `PHASE 3: REFACTORING COMPLETE`.

Os relatórios e o código refatorado ficam nessa cópia; apague a pasta `../refactor-repro` quando terminar.

### 4.3 Rodar os projetos refatorados

| Projeto | Subir | Porta padrão |
|---|---|---|
| `code-smells-project` | `python -m venv .venv && source .venv/bin/activate`; `pip install -r requirements.txt`; `cp .env.example .env` (preencha `SECRET_KEY`, `ADMIN_PASSWORD` e `SEED_CUSTOMER_PASSWORD`); `set -a; source .env; set +a`; `python app.py` | 5000 (`APP_PORT`) |
| `ecommerce-api-legacy` | `npm install`; `cp .env.example .env` (preencha `ADMIN_TOKEN` e `SEED_USER_PASSWORD`); `set -a; source .env; set +a`; `npm start` | 3000 (`PORT`) |
| `task-manager-api` | `python -m venv .venv && source .venv/bin/activate`; `pip install -r requirements.txt`; `cp .env.example .env` (preencha `SECRET_KEY`, `SEED_ADMIN_PASSWORD`, `SEED_USER_PASSWORD`); `python seed.py`; `python app.py` | 5000 (`APP_PORT`) |

`code-smells-project` e `ecommerce-api-legacy` não leem o `.env` sozinhos, por isso o `source`; o `task-manager-api` lê o arquivo com `python-dotenv`.

Variáveis, acesso por rota e outros detalhes estão no README de cada projeto: [`code-smells-project`](code-smells-project/README.md#como-rodar), [`ecommerce-api-legacy`](ecommerce-api-legacy/README.md#como-rodar) e [`task-manager-api`](task-manager-api/README.md#como-rodar).

`code-smells-project` e `task-manager-api` usam a mesma porta padrão; para subir os dois juntos, mude
`APP_PORT` de um deles.

### 4.4 Validação

**Estrutura.** Na raiz do repositório, com a aplicação parada ou não:

```bash
<projeto>/.claude/skills/refactor-arch/scripts/arch-check.sh <projeto>   # exit 0 = PASS
```

**Contrato HTTP.** O `api-test.sh` exige a aplicação no ar e um banco descartável, porque escreve e
apaga dados. Nos três projetos, um banco fora de uma pasta temporária (`/tmp`, `/private/tmp`,
`/var/folders` ou `$TMPDIR`) é recusado com "not isolated" e exit 2. O `ecommerce-api-legacy` também
aceita `DB_FILE=:memory:`, mas aí as checagens de banco são puladas. Rode um projeto por vez, com as
dependências instaladas e o `.env` preenchido (§4.3):

```bash
# code-smells-project
cd code-smells-project
set -a; source .env; set +a
export DB_PATH="$(mktemp -d)/loja-test.db" APP_LOG_FILE="$(mktemp -d)/app.log"
python app.py > "$APP_LOG_FILE" 2>&1 &
sleep 3
./api-test.sh                    # TOTAL: 173 checks | failures: 0 | skipped: 0
kill $!; cd ..

# ecommerce-api-legacy
cd ecommerce-api-legacy
set -a; source .env; set +a
export DB_FILE="$(mktemp -d)/loja.sqlite" APP_LOG="$(mktemp -d)/app.log"
node src/app.js > "$APP_LOG" 2>&1 &
sleep 3
./api-test.sh                    # TOTAL: 100 checks | failures: 0 | skipped: 0
kill $!; cd ..

# task-manager-api
cd task-manager-api
set -a; source .env; set +a
export DATABASE_URL="sqlite:///$(mktemp -d)/tasks.db" APP_LOG_FILE="$(mktemp -d)/app.log"
python seed.py
python app.py > "$APP_LOG_FILE" 2>&1 &
sleep 3
./api-test.sh                    # TOTAL: 217 checks | failures: 0 | skipped: 0
kill $!; cd ..
```

O exit 0 do `api-test.sh` significa sem falhas. O `api-test.sh` do `code-smells-project` apaga tudo no
final: para repetir, suba a aplicação com um `DB_PATH` novo.

Como alternativa manual, cada projeto traz um arquivo `*-api-curls.http` com as mesmas requisições para o cliente HTTP do JetBrains (GoLand, IntelliJ, PyCharm etc.). Preencha as variáveis do topo do arquivo, suba a aplicação com um banco novo e execute as requisições na ordem, porque tokens e ids são guardados pelas respostas. O cabeçalho de cada arquivo indica o que apaga dados e o que depende de configuração.
