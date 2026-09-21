# Construção da Skill

[← README](../README.md) · [Análise Manual](manual-analysis.md) · [Resultados](results.md) · [Evolução do Uso de IA](ai-evolution.md) · [Estrutura do Projeto](project-structure.md) · [Enunciado Original](challenge-original.md)

> Decisões de design completas do `SKILL.md` e dos arquivos de referência — o resumo condensado, com a árvore da skill e a tabela de `references/`, está na [seção 2 do README](../README.md#2-construção-da-skill).

---

## 2.1 Objetivo da Skill

A skill `refactor-arch` foi desenhada para replicar, de forma automatizada, o processo de análise manual feito na [seção 1 do README](../README.md#1-análise-manual): dado qualquer projeto backend, ela deve (1) detectar a stack e a arquitetura atual sem suposições prévias, (2) auditar o código contra um catálogo de anti-patterns e gerar um relatório estruturado, pausando para confirmação humana, e (3) refatorar o projeto para MVC preservando 100% do comportamento observável (endpoints, formatos de resposta, exceto correções de segurança intencionais como redação de senha).

## 2.2 Estrutura da Skill

```
.claude/skills/refactor-arch/
├── SKILL.md                                # visão geral + fluxo das 3 fases (carregado sempre)
├── references/                             # carregados sob demanda, por fase
│   ├── project-analysis.md                 # Fase 1
│   ├── anti-patterns-catalog.md            # Fase 2
│   ├── audit-report-template.md            # Fase 2
│   ├── architecture-guidelines.md          # Fase 3
│   ├── refactoring-playbook.md             # Fase 3
│   └── verification-recipes.md             # Fase 3, passo 6
└── scripts/                                # executáveis da skill
    └── arch-check.sh                       # Fase 3, passo 6 — verificação de AP-16
```

O design segue o princípio de *progressive disclosure*: o `SKILL.md` funciona como um índice/prompt enxuto (frontmatter + fluxo), e cada arquivo de referência só é lido quando a fase correspondente começa — a Fase 1 nunca precisa carregar o playbook de refatoração, por exemplo. Isso mantém o contexto necessário em cada etapa proporcional ao que ela realmente exige.

## 2.3 SKILL.md

O `SKILL.md` (código-fonte completo em [`code-smells-project/.claude/skills/refactor-arch/SKILL.md`](../code-smells-project/.claude/skills/refactor-arch/SKILL.md)) contém:

- **Frontmatter** com `name: refactor-arch` (fixo, exigido pelo enunciado) e uma `description` em inglês escrita para casar com a forma como o usuário pediria a tarefa ("analyze, audit, or refactor a project's architecture"), já que a invocação da skill é dirigida pela similaridade entre a descrição e o pedido do usuário.
- A **escala de severidade** (CRITICAL/HIGH/MEDIUM/LOW), resumida no próprio `SKILL.md` e detalhada nos sinais de detecção em `anti-patterns-catalog.md`.
- O **fluxo das 3 fases**, cada uma com um formato de saída fixo (blocos `================================`) para garantir que o output seja parseável e consistente independentemente do projeto.
- Uma seção final de **"Non-negotiable rules"**: nunca modificar arquivo antes da confirmação da Fase 2; todo finding deve citar arquivo/linha reais (nunca "chutar"); nunca assumir Python/Flask; preservar comportamento observável; nunca reportar sucesso da Fase 3 com uma regressão conhecida.

## 2.4 Arquivos de Referência

| Arquivo | Fase | Área de conhecimento ([enunciado](challenge-original.md#2-criação-da-skill)) | Conteúdo |
|---|---|---|---|
| `project-analysis.md` | 1 | Análise de projeto | Heurísticas de detecção de linguagem (extensões/manifests), framework, banco de dados, domínio e classificação da arquitetura atual (monolítica / parcialmente em camadas / já em MVC) |
| `anti-patterns-catalog.md` | 2 | Catálogo de anti-patterns | 17 anti-patterns (AP-01–AP-17) com sinais de detecção agnósticos de linguagem, distribuídos nas 4 severidades, incluindo detecção de APIs deprecated |
| `audit-report-template.md` | 2 | Template de relatório | Formato exato do `ARCHITECTURE AUDIT REPORT` (cabeçalho, `## Summary`, `## Findings` ordenados por severidade, regras de preenchimento) |
| `architecture-guidelines.md` | 3 | Guidelines de arquitetura | Responsabilidades de Models/Views-Routes/Controllers, camadas de suporte opcionais (config, services, middlewares, entry point), layouts por stack (Flask, Express) e regra para projetos parcialmente em camadas |
| `refactoring-playbook.md` | 3 | Playbook de refatoração | 16 padrões de transformação (RP-01–RP-16, acima do mínimo de 8 exigido pelo [enunciado](challenge-original.md#2-criação-da-skill)) com exemplos antes/depois em Python e Node.js, cada um referenciando o(s) AP-xx que resolve |
| `verification-recipes.md` | 3 (passo 6) | Guidelines de arquitetura | Sinais de persistência por stack (Python, JS/TS, Go, Java/Kotlin, Ruby, PHP, C#), configuração do `arch-check.sh` e o procedimento para derivar padrões numa stack não listada |

A skill também empacota um executável próprio, `scripts/arch-check.sh`: a verificação estrutural do AP-16 exigida no passo 6 da Fase 3. Ele detecta as linguagens presentes, seleciona os arquivos de rota/view e procura os sinais de persistência da stack correspondente. Se o projeto auditado já tiver uma verificação equivalente, a skill roda a dele; caso contrário, roda e instala essa. Sair com código 2 ("nenhum arquivo de rota identificado") é reportado como INCONCLUSIVE, nunca como aprovação — a distinção veio de um falso PASS real: rodando as Fases 1 e 2 contra um projeto Go/Gin externo, o checker aprovou arquivos de rota cheios de violações porque em Go a persistência é função de pacote, não método de receiver — relatado no parágrafo *Correção* de [Bug Encontrado Após a Entrega](results.md#bug-encontrado-após-a-entrega) e detalhado em [Evolução do Uso de IA, 7.3](ai-evolution.md#73-modo-headless-e-ci).

Cada finding do relatório de Fase 2 referencia um `AP-xx`, e cada `AP-xx` do catálogo é referenciado por um ou mais `RP-xx` do playbook — esse mapeamento cruzado é o que permite à Fase 3 decidir mecanicamente qual transformação aplicar a partir do próprio relatório da Fase 2, em vez de reinventar a correção a cada execução.

## 2.5 Catálogo de Anti-patterns

O catálogo tem 17 entradas (acima do mínimo de 8 exigido pelo enunciado em [Criação da Skill](challenge-original.md#2-criação-da-skill), "Requisitos da skill"), distribuídas assim:

- **CRITICAL (5):** AP-01 SQL Injection, AP-02 Segredos/credenciais hardcoded, AP-03 Hashing de senha quebrado/falso, AP-04 Dado sensível vazado via serialização, AP-17 Ausência de autenticação/autorização em endpoint sensível.
- **HIGH (4):** AP-05 God Class, AP-06 Lógica de negócio duplicada, AP-07 Estado mutável global, AP-16 Persistência/ORM chamada direto na rota.
- **MEDIUM (4):** AP-08 N+1, AP-09 Ausência de paginação, AP-10 Camada de código morta/desconectada, AP-11 Uso de API deprecated.
- **LOW (4):** AP-12 Logging via print/console, AP-13 Configuração/valores mágicos hardcoded, AP-14 Imports não utilizados, AP-15 Idioma/nomenclatura inconsistente.

Os 15 primeiros foram escolhidos porque apareceram, na prática, em pelo menos um dos 3 projetos durante a [análise manual](../README.md#1-análise-manual) — nenhum é hipotético. Os dois últimos entraram depois, pelo mesmo critério e pelo motivo oposto: descrevem problemas reais que atravessaram auditorias inteiras justamente por não estarem catalogados. O AP-16 ficou no `task-manager-api` e passou pela auditoria original ([seção Bug Encontrado Após a Entrega](results.md#bug-encontrado-após-a-entrega)); o AP-17 é o CRITICAL de ausência total de autenticação que atravessou três rodadas do `ecommerce-api-legacy` e só apareceu na rodada 4 ([`audit-project-2-part4.md`](../reports/audit-project-2-part4.md)), quando os testes manuais de endpoint foram escritos. Ambos têm padrão de correção correspondente no playbook — RP-14 e RP-16. A detecção de API deprecated (AP-11) foi incluída como sua própria categoria (e não apenas um exemplo dentro de outra) porque o enunciado exige isso explicitamente; ela cobre tanto Python (`datetime.utcnow()`, `imp`, `flask.ext.*`) quanto Node.js (`new Buffer()`, `crypto.createCipher`), e foi validada na prática no `task-manager-api`, que usa `datetime.utcnow()` em 18 pontos do código.

## 2.6 Estratégia Agnóstica de Tecnologia

Três decisões de design garantem que a skill funcione igualmente bem em Python/Flask e Node.js/Express, sem hardcode de stack:

1. **Detecção, nunca suposição.** `project-analysis.md` define sinais por linguagem (manifests, extensões, imports no entry point) e instrui a Fase 1 a inferir a stack a cada execução — o `SKILL.md` reforça isso explicitamente na lista de "Non-negotiable rules" ("Do not assume Python/Flask: detect the stack fresh for every project this skill runs against").
2. **Sinais de detecção descritos por padrão, não por sintaxe de uma linguagem.** Cada `AP-xx` descreve o *padrão* (ex: "query montada por concatenação de string com valor controlado pelo cliente") e cita exemplos equivalentes nas duas linguagens, em vez de regex específico de uma stack.
3. **Playbook com exemplo antes/depois nas duas linguagens quando aplicável**, e instrução explícita para aplicar "o mesmo princípio" quando a stack real não corresponder a nenhum dos exemplos — cobrindo qualquer quarta linguagem que venha a ser usada no futuro.

A prova concreta dessa estratégia é a própria execução nos 3 projetos: a mesma skill, copiada sem alteração de `code-smells-project/` para `ecommerce-api-legacy/` (Node.js) e `task-manager-api/` (Python, mas parcialmente em camadas), produziu relatórios e refatorações corretos nas 3 stacks/níveis de organização ([seção 3 do README](../README.md#3-resultados)).

## 2.7 Fluxo de Execução

1. **Fase 1 — Análise:** lê `project-analysis.md`, detecta linguagem/framework/dependências/domínio/arquitetura, e imprime o bloco `PHASE 1: PROJECT ANALYSIS` no formato fixo definido no `SKILL.md`.
2. **Fase 2 — Auditoria:** lê `anti-patterns-catalog.md` e `audit-report-template.md`, varre cada arquivo-fonte identificado na Fase 1 contra os 16 `AP-xx`, exige no mínimo 5 findings (≥1 CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW) com arquivo/linha reais, ordena por severidade e imprime o `ARCHITECTURE AUDIT REPORT`. Em seguida **para e pede confirmação explícita** — nenhum arquivo é tocado antes do `y`/`yes`/`proceed` do usuário.
3. **Fase 3 — Refatoração:** só começa após a confirmação; lê `architecture-guidelines.md` e `refactoring-playbook.md`, projeta o layout MVC adequado à stack detectada (adaptando, não reconstruindo, quando já existe alguma camada), aplica o `RP-xx` correspondente a cada finding confirmado, e valida o resultado (boot da aplicação + endpoints originais respondendo) antes de imprimir o bloco `PHASE 3: REFACTORING COMPLETE`.

## 2.8 Desafios e Soluções

- **Risco de finding fabricado ("alucinação" de linha/arquivo):** a regra mais repetida em todo o conjunto de arquivos é "nunca reportar um finding sem arquivo/linha real — reabra o arquivo se não tiver certeza". Isso foi reforçado tanto no catálogo quanto nas "Non-negotiable rules" do `SKILL.md`, e na prática os 3 relatórios em `reports/` citam ranges de linha específicos e verificáveis.
- **Projeto parcialmente em camadas (`task-manager-api`) exigindo tratamento diferente de um monolito:** um projeto que já tem `models/routes/services/utils` não deve ser reconstruído do zero — só as responsabilidades erradas dentro de cada camada precisam ser corrigidas. `architecture-guidelines.md` trata esse caso como uma categoria própria ("Partially-layered projects"), instruindo a manter os nomes de pasta existentes e apenas mover a lógica para o lugar certo — foi exatamente o que aconteceu na Fase 3 desse projeto: nenhuma camada existente foi renomeada ou reconstruída — só `config/` e `services/report_service.py` foram criados, o resto foram ajustes internos nos arquivos existentes (ver [Resultados](results.md)).
- **Preservar comportamento observável mesmo corrigindo falhas de segurança:** redigir o hash de senha da resposta de `/login` ou de `/users` é, por definição, uma mudança de response shape — mas é uma mudança *desejada*. A solução foi documentar essa exceção explicitamente em `architecture-guidelines.md` ("No endpoint may change its response shape except to redact a previously-leaked sensitive field").
- **Nomear o arquivo de template do relatório:** optou-se por `audit-report-template.md` (em vez de `report-template.md`) para deixar explícito, só pelo nome, que o arquivo é o template do relatório de *auditoria* da Fase 2 e não de qualquer outro tipo de relatório que a skill possa vir a gerar.
- **Tornar a Fase 3 mecânica e não ad hoc:** sem um mapeamento entre finding e correção, a Fase 3 dependeria de o agente "lembrar" a correção certa a cada execução. O esquema de IDs cruzados `AP-xx ↔ RP-xx` (seção 2.4) resolve isso: a Fase 3 lê a `Recommendation` de cada finding confirmado e aplica o `RP-xx` citado, o que tornou a refatoração consistente nas 3 execuções reais.
