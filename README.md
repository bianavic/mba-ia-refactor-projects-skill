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
da verdade desta análise. Descrição, impacto, critério de severidade e validação em execução de cada
achado estão em [`docs/manual-analysis.md`](docs/manual-analysis.md).

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
com cópias idênticas nos outros dois projetos. Detalhes em [`docs/skill-construction.md`](docs/skill-construction.md).

**Estrutura.** `SKILL.md` (frontmatter, fluxo das 3 fases, regras inegociáveis) mais referências em
Markdown em `references/`, carregadas sob demanda por fase, e dois scripts em `scripts/`
(`arch-check.sh` e `completion-box.sh`):

| Área exigida | Arquivo | Conteúdo |
|---|---|---|
| Análise de projeto | `project-analysis.md` | Detecção de linguagem, framework, banco, arquitetura e inventário de endpoints |
| Catálogo de anti-patterns | `anti-patterns-catalog.md` | 23 anti-patterns pela severidade base: 7 CRITICAL, 4 HIGH, 8 MEDIUM, 4 LOW. AP-04, AP-06, AP-12, AP-18 e AP-21 têm regra própria para subir ou descer (ex.: AP-06 é CRITICAL quando um único arquivo junta banco, rotas e regra, ou quando a separação é só nominal, com o arquivo de rotas ou um controller executando SQL direto por fora da camada de dados) |
| Template de relatório | `audit-report-template.md` | Formato fixo do relatório da Fase 2 |
| Guidelines de arquitetura | `architecture-guidelines.md` | Camadas MVC e tabela de decisão de colocação |
| Playbook de refatoração | `refactoring-playbook.md` | 22 padrões antes/depois (Python; 17 também em JavaScript/Node), um ou mais por anti-pattern |

Há ainda `phase3-validation.md` (validação da Fase 3: `api-test.sh`, `arch-check.sh`, checagem por
finding, anti-tautologia, log de validação, evidências da caixa final). `arch-check.sh` faz a
verificação estrutural agnóstica de stack; `completion-box.sh` gera a caixa
`PHASE 3: REFACTORING COMPLETE` e só a imprime quando as pré-condições passam. As regras das
decisões abertas e o formato do plano ficam no próprio `SKILL.md`, na Fase 2.
As três cópias da skill (uma por projeto) são idênticas.

**Catálogo e por quê.** Os 23 anti-patterns vêm de três fontes: os achados da análise manual (§1),
os exemplos de cada nível da escala de severidade do enunciado e os desafios que apareceram ao rodar a
skill. Todos são usados: cada `AP-xx` aparece em pelo menos um dos três relatórios.

| Severidade base | Anti-patterns | Por que entraram |
|---|---|---|
| CRITICAL (7) | AP-01 SQL injection · AP-02 segredos hardcoded · AP-03 hash de senha quebrado/ausente · AP-04 dado sensível na serialização · AP-05 falta de autenticação/autorização · AP-17 escalada de privilégio no auto-cadastro · AP-20 endpoint de execução arbitrária | AP-01 e AP-02 são os exemplos de CRITICAL do enunciado e estão na §1 (SQL concatenado no code-smells; segredos nos 3 projetos). AP-03 e AP-04 generalizam o texto plano, o `badCrypto` e o MD5 da §1 e a senha/hash devolvidos nas respostas. AP-05 cobre as rotas de admin e de dados pessoais abertas nos 3 projetos, e AP-20 o `POST /admin/query` do code-smells, que executa SQL do cliente. AP-17 veio de um desafio: a Fase 3 criou o papel de admin e o cadastro aceitava `role` do corpo. Todos expõem dado ou dão controle a quem não deveria tê-lo |
| HIGH (4) | AP-06 God Class · AP-07 regra de negócio duplicada · AP-08 estado global mutável · AP-22 orquestração fora de um Service | Dois exemplos de HIGH do enunciado: regra de negócio presa nas rotas/controllers (AP-22, o padrão do task-manager) e estado global mutável (AP-08, `globalCache`/`totalRevenue` do ecommerce). AP-06 aplica a definição geral de HIGH (forte violação de MVC) e sobe a CRITICAL quando a separação de responsabilidades é violada por completo: banco, regra e roteamento numa classe só (ecommerce) ou separação só nominal, com SQL cru no arquivo de rotas (code-smells, §1). Rotas que chamam o ORM, como no task-manager, ficam no AP-22. AP-07 vem da regra `is_overdue` do task-manager, reescrita em várias rotas: duplicação sozinha seria MEDIUM no enunciado, mas aqui a regra duplicada é de domínio e saiu do model, o que a torna violação de MVC. Não expõem dado, mas impedem testar e mudar uma parte sem as outras |
| MEDIUM (8) | AP-09 N+1 · AP-10 sem paginação · AP-11 camada morta/desconectada · AP-12 APIs deprecated e versões vulneráveis/EOL · AP-18 dado pessoal em log · AP-19 direitos do titular incompletos · AP-21 validação de entrada ausente · AP-23 módulos soltos na raiz | AP-09 e AP-21 são exemplos de MEDIUM do enunciado; AP-09 e AP-10 aparecem nos 3 projetos (§1.4). AP-12 atende a exigência de detectar APIs deprecated e cobre também versões fixadas com advisory. AP-11 vem do serviço de notificação que nenhuma rota usa. AP-18 e AP-19 vieram de um desafio (a lente de dado pessoal): o cartão no log do ecommerce e a falta de exclusão, exportação e retenção nos 3. AP-23 cobre `database.py`, `seed.py` e afins na raiz, que o layout MVC precisa mover. Custam desempenho, manutenção ou conformidade, sem exposição imediata (AP-12, AP-18 e AP-21 sobem quando há) |
| LOW (4) | AP-13 `print`/`console.log` como log · AP-14 configuração/valores mágicos · AP-15 imports não usados · AP-16 nomenclatura inconsistente | Os exemplos de LOW do enunciado (nomenclatura ruim, *magic numbers*) e os LOW da §1: `print()`/`console.log` nos 3, categorias hardcoded no code-smells, imports não usados no task-manager e idiomas misturados no ecommerce. Afetam legibilidade, não comportamento |

**Decisões de design**
- **Catálogo → playbook.** Cada finding cita um `AP-xx` e um `RP-xx`; a Fase 3 aplica o padrão que o plano aprovado nomeia, em vez de improvisar. O catálogo inclui detecção de APIs deprecated e de versões fixadas vulneráveis ou EOL (AP-12).
- **Agnóstica.** A stack é detectada a cada execução, os sinais descrevem padrões e não sintaxe, e stack sem cobertura é relatada como lacuna, nunca como aprovação. Python/Flask e Node.js/Express são o perfil coberto.
- **Pausa obrigatória.** A Fase 2 grava o relatório, pergunta cada decisão em aberto e só segue após `y` à pergunta literal do enunciado; antes disso o único arquivo escrito é o relatório em `reports/`, e nenhum arquivo do projeto muda.
- **Prova, não declaração.** A Fase 3 só conclui com boot, `api-test.sh` exit 0, `arch-check.sh` exit 0 e artefatos em disco; cada `✓` da caixa final exige sua evidência.

**Desafios** (tabela completa em [`docs/skill-construction.md`](docs/skill-construction.md#desafios-e-como-a-skill-os-trata)):
- **Finding fabricado:** regra de `file:line` real, reaberto e conferido, nas regras inegociáveis e no catálogo.
- **Projeto já em camadas:** a categoria *Partially-layered projects* manda manter as pastas existentes e mover só a responsabilidade errada.
- **Segurança sem quebrar o contrato:** a resposta de um endpoint só muda para corrigir um defeito e na opção que o usuário escolheu na Fase 2; o plano marca essas linhas como `[CONTRACT_CHANGE]` com a origem `you chose`, e nenhuma opção remove endpoint.
- **Fase 3 ad hoc:** mapa `AP-xx ↔ RP-xx` faz cada finding apontar para a correção a aplicar.
- **Falha que a Fase 2 não viu:** a guarda de admin era contornável por `role` no cadastro; virou o AP-17.
- **Projetos sem relatório ou evidência:** a skill passou a salvar relatório e log em disco e a tratar a ausência deles como fase incompleta.
- **Dado pessoal fora do catálogo:** criados o AP-18 (PII em log) e o AP-19 (direitos do titular) e a lente de proteção de dados no template.

## 3. Resultados

## 4. Como Executar
