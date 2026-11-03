# Construção da Skill — detalhes

[← README §2](../README.md#2-construção-da-skill)

Fonte da verdade: `.claude/skills/refactor-arch/` (v3.0.0), versionada nos três projetos com
conteúdo idêntico. Referência: [`code-smells-project/.claude/skills/refactor-arch/`](../code-smells-project/.claude/skills/refactor-arch/SKILL.md).

## Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                      # frontmatter + fluxo das 3 fases + regras inegociáveis
├── references/                   # carregados sob demanda, por fase
│   ├── project-analysis.md       # Fase 1
│   ├── anti-patterns-catalog.md  # Fase 2
│   ├── audit-report-template.md  # Fase 2
│   ├── architecture-guidelines.md # Fase 3
│   ├── refactoring-playbook.md   # Fase 3
│   └── refactoring-validation.md # Fase 3 — api-test.sh, arch-check.sh, anti-tautologia, log, evidências
└── scripts/
    ├── arch-check.sh             # verificação estrutural, agnóstica de stack
    └── completion-box.sh         # gera a caixa "PHASE 3: REFACTORING COMPLETE" só se as pré-condições passam
```

O `SKILL.md` é um prompt enxuto: cada fase só lê as referências de que precisa (*progressive
disclosure*). O frontmatter define:

- `name: refactor-arch`;
- `description`: o que a skill faz (auditoria e refatoração MVC de uma API HTTP de backend), que
  ela roda só via `/refactor-arch` e quando não usar (edições pontuais, frontends, projetos sem
  backend HTTP);
- `disable-model-invocation: true`: a skill roda só quando chamada com `/refactor-arch`;
- `allowed-tools`: só os dois scripts empacotados, que a skill executa e nunca lê;
- `metadata.version: 3.0.0`.

## Áreas de conhecimento exigidas pelo enunciado

| Área | Arquivo | Conteúdo |
|---|---|---|
| Análise de projeto | `project-analysis.md` | Heurísticas de linguagem, framework, banco, arquitetura atual, contagem de arquivos/linhas e inventário de endpoints |
| Catálogo de anti-patterns | `anti-patterns-catalog.md` | 23 anti-patterns (AP-01–AP-23) com sinais de detecção e severidade |
| Template de relatório | `audit-report-template.md` | Formato fixo do relatório, onde salvá-lo e regras de re-execução |
| Guidelines de arquitetura | `architecture-guidelines.md` | Responsabilidade de cada camada, tabela de decisão de colocação, projetos já parcialmente em camadas |
| Playbook de refatoração | `refactoring-playbook.md` | 22 padrões (RP-01–RP-22) com exemplos antes/depois em Python; 17 também em JavaScript/Node (Express) |

## Catálogo

| Severidade | Anti-patterns |
|---|---|
| CRITICAL (7) | AP-01 SQL injection · AP-02 segredos hardcoded · AP-03 hash de senha quebrado/ausente · AP-04 dado sensível vazado na serialização · AP-05 falta de autenticação/autorização · AP-17 escalada de privilégio no auto-cadastro · AP-20 endpoint de execução arbitrária |
| HIGH (4) | AP-06 God Class · AP-07 regra de negócio duplicada · AP-08 estado global mutável · AP-22 orquestração fora de um Service |
| MEDIUM (8) | AP-09 N+1 · AP-10 sem paginação · AP-11 camada morta/desconectada · AP-12 APIs deprecated e versões vulneráveis/EOL · AP-18 dado pessoal em log · AP-19 direitos do titular incompletos · AP-21 validação de entrada ausente · AP-23 módulos soltos na raiz |
| LOW (4) | AP-13 `print`/`console.log` como log · AP-14 configuração/valores mágicos · AP-15 imports não usados · AP-16 nomenclatura inconsistente |

A tabela mostra a severidade base. AP-04, AP-06, AP-12, AP-18 e AP-21 têm regra própria para subir
ou descer; por exemplo, AP-06 sobe a CRITICAL quando banco, regra e roteamento estão numa classe só
ou quando a separação é só nominal (o arquivo de rotas executa SQL direto, por fora da camada de
dados).

AP-12 é um portão obrigatório da Fase 2: checa APIs deprecated **e** versões fixadas desatualizadas ou
com avisos conhecidos. Um componente cuja consulta externa falhou em todas as fontes fica `BLOCKED`,
nunca `clean`, e vira decisão em aberto: tentar de novo ou seguir com ele não verificado, como linha
`left open`. Cada `AP-xx` tem um ou mais `RP-xx` no playbook (a tabela no topo do
`refactoring-playbook.md` faz o mapeamento) e o relatório cita o `RP-xx` na `Recommendation`.

## Agnóstica de tecnologia

1. **Detecção em tempo de execução.** A Fase 1 infere a stack de manifests, extensões e imports; a
   regra 1 proíbe assumir a stack de uma execução anterior.
2. **Sinais por padrão, não por sintaxe.** Cada AP descreve o padrão e cita equivalentes nas
   stacks cobertas (Python/Flask e Node.js/Express). O playbook mostra cada RP em Python, em
   JavaScript ou nos dois, sempre com nomes genéricos (`<table>`, `<entity>`) para serem
   traduzidos para o projeto analisado.
3. **Cobertura declarada.** Outras stacks só são inspecionadas com evidência suficiente; sinal
   não suportado é relatado como lacuna de cobertura, nunca como aprovação estrutural.
4. **Verificação mecânica configurável.** `arch-check.sh` acha rotas, models e controllers por
   heurística e aceita ajuste (`ROUTE_DIRS`, `CONTROLLER_DIRS`, …) em `.arch-check.conf`.

## Fluxo

1. **Fase 1 — Análise:** detecta stack, domínio, arquitetura, arquivos/linhas e endpoints. Confere com `command -v` as ferramentas que a Fase 3 vai usar (`bash`, `curl`, um parser JSON e, quando preciso, o CLI do banco). Imprime a caixa fixa do enunciado e, logo abaixo, `Lines:`, `Endpoints:` e `Tooling:`.
2. **Fase 2 — Auditoria:** varre cada arquivo contra o catálogo e roda o portão AP-12; um componente `BLOCKED` vira decisão em aberto. Roda o `arch-check.sh` como pista de AP-06/AP-22/AP-23 e confirma cada pista abrindo o arquivo. Salva `reports/audit-project-<N>.md` e confere com `test -s` e com a pergunta literal como última linha. Depois:
   - imprime o relatório e a lista `Checked, no findings`;
   - antes da pergunta sobre autenticação, apresenta a tabela de acesso por rota para o usuário confirmar;
   - pergunta cada decisão em aberto (uma por pergunta, opções com o resíduo explícito) e imprime o plano de refatoração;
   - termina com a linha literal `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`.

   Nenhum arquivo do projeto muda antes do `y`; o único arquivo escrito é o relatório. O `y` aprova o plano e também o que a Fase 3 deriva dele sem nova decisão: o layout gerado pela tabela de colocação e os artefatos de validação.
3. **Fase 3 — Refatoração:**
   - imprime a tabela de layout antes de escrever código: uma linha por arquivo resultante (arquivo → camada → critério), e cada arquivo original dividido mostra para onde foi cada parte;
   - aplica o `RP-xx` de cada linha do plano;
   - gera e roda o `api-test.sh` e roda o `arch-check.sh`;
   - prova que as checagens podem falhar, com um defeito injetado numa cópia descartável;
   - salva o log em `evidence/logs/` e escreve *Future improvements* no README do projeto;
   - roda o `completion-box.sh`, que só imprime a caixa de conclusão se as pré-condições passam, e por baixo dela imprime `## Validation evidence` e `## Future improvements`. O `✓ Zero anti-patterns remaining` significa que cada finding foi resolvido ou deixado `left open` pelo usuário; a linha `Findings:`, logo abaixo da caixa, traz as contagens.

## Desafios e como a skill os trata

| Desafio | Como foi resolvido |
|---|---|
| **Finding fabricado** — o maior risco de uma auditoria feita por LLM é citar arquivo e linha que não existem | Regra 2 das *Non-negotiable rules* do `SKILL.md` (todo finding cita um `file:line` real, conferido abrindo o arquivo) e item *Evidence* da draft validation do catálogo (hit de grep é pista, não citação). O *sweep* da draft validation procura o mesmo sinal em todos os arquivos antes de fechar o `File:`, para que cada finding liste todos os seus locais |
| **Projeto parcialmente em camadas** — o Projeto 3 já tinha `models/routes/services/utils`; reconstruí-lo do zero seria errado, e aceitá-lo como pronto também | `architecture-guidelines.md` ganhou a categoria *Partially-layered projects*: manter os nomes de pasta existentes e mover só a responsabilidade errada. Query em rota vai para o Model e o fluxo da requisição para um Controller (criando `controllers/` quando não existe); regra duplicada vai para o Model da sua entidade; um `services/` morto é conectado ou removido; módulos de apoio soltos se juntam às pastas que já existem |
| **Corrigir segurança sem quebrar contrato** — redigir a senha de `/login` é, por definição, mudar o response shape | Regra 5 das *Non-negotiable rules*: a resposta só muda para corrigir um defeito e como o usuário decidiu na Fase 2. No plano, essa linha é `[CONTRACT_CHANGE]` (sempre para RP-09, RP-16, RP-19 e RP-20) com a origem `you chose`; sem ela, é erro de plano e a pergunta volta. Nenhuma opção remove endpoint |
| **Fase 3 ad hoc** — sem vínculo entre achado e correção, o agente teria de "lembrar" a solução a cada execução | Esquema de IDs cruzados `AP-xx ↔ RP-xx`: a Fase 3 lê a `Recommendation` de cada finding confirmado e aplica o `RP-xx` citado. O `refactoring-validation.md` §4 exige, antes de dar um finding por resolvido, uma checagem por local citado que poderia ter falhado. O resultado vai para a evidência impressa sob a caixa de conclusão |
| **A Fase 3 pode abrir a falha que a Fase 2 não viu** — ao adicionar `@admin_required`, o Projeto 3 passou a ter papel privilegiado, e `POST /users` aceitava `role` do corpo: a guarda era contornável por um cadastro | Descoberto numa versão anterior da skill. Rendeu **AP-17** (escalação por campo de cadastro), cuja correção é uma linha do `RP-16`: campo de privilégio só gravável por administrador. Quais rotas proteger, e como, o usuário decide na Fase 2, antes da pergunta `[y/n]` |
| **Execução sem relatório ou sem evidência** — uma rodada que não deixa relatório nem log não pode ser auditada, e um resumo impresso some com a sessão | A skill vai com cada projeto, e as duas fases gravam o que produzem antes de seguir. A Fase 2 salva o relatório e o confirma (`test -s` e a pergunta literal como última linha) antes do gate. A Fase 3 grava o log em `evidence/logs/` (`refactoring-validation.md` §6) e só imprime `Report:`/`Log:` depois de `test -s`. A lista `Checked, no findings`, impressa após o relatório, separa "verificado, nada encontrado" de "não verificado". O `completion-box.sh` recusa a caixa sem um log válido em disco |
| **O catálogo era forte em estrutura e fraco em ciclo de vida do dado pessoal** — nenhum anti-pattern perguntava por quanto tempo o dado fica guardado | Rendeu **AP-18** (PII em log) e **AP-19** (direitos do titular incompletos: exclusão, exportação e retenção), mais a lente de proteção de dados (LGPD, GDPR, PCI-DSS) no template de relatório, que orienta `Impact` e `Recommendation` sem mudar a severidade |
