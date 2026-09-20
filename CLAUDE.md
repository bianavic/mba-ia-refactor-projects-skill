# mba-ia-refactor-projects-skill

Entrega do desafio de MBA: uma skill (`refactor-arch`) que audita e refatora projetos
legados para MVC, mais os 3 projetos legados em que ela foi executada. O produto
avaliado é o conjunto **skill + relatórios + código refatorado + README.md**.

```
code-smells-project/     Projeto 1 — Python/Flask, SQLite cru       (e-commerce)
ecommerce-api-legacy/    Projeto 2 — Node.js/Express, sqlite3       (LMS/e-learning)
task-manager-api/        Projeto 3 — Python/Flask + SQLAlchemy      (task manager)
reports/                 relatórios de auditoria (saída da Fase 2)
evidence/                screenshots + logs citados na seção 3.4 do README
docs/                    deep dives + `challenge-original.md` (o enunciado do desafio)
scripts/                 `sync-docs.sh` — regenera as partes geradas do README e de docs/
```

## A skill vive em triplicata

`.claude/skills/refactor-arch/` existe **idêntica** dentro dos 3 projetos — é exigência
do enunciado ([seção 3 do enunciado](docs/challenge-original.md#3-execução-da-skill)),
não duplicação acidental.

- Qualquer edição em `SKILL.md`, `references/` ou `scripts/` deve ser replicada nas 3 cópias.
- Confirme antes de encerrar a tarefa:
  `diff -r code-smells-project/.claude/skills/refactor-arch <outro-projeto>/.claude/skills/refactor-arch`
- A skill é escrita em **inglês**. Mantenha assim, mesmo que a conversa seja em português.

## Relatórios

- `reports/audit-project-N.md` — N = 1 (code-smells), 2 (ecommerce), 3 (task-manager)
- Re-auditoria de um projeto já refatorado vai para `audit-project-N-part2.md`, com uma
  seção `## Resolved since audit-project-N.md` no topo. **Nunca sobrescreva** um relatório
  anterior: ele é a evidência do estado "antes".
- A Fase 2 **salva sozinha** em `reports/`: quem manda é
  `references/audit-report-template.md` (§ Execution order, passo 3), que resolve a raiz do
  repo com `git rev-parse --show-toplevel`. Não é passo manual. O que continua manual é o
  rollup para README/`docs/` — veja a seção abaixo.

## Antes de dar uma refatoração por concluída

Rode, dentro da pasta do projeto alterado, **capturando a saída** em
`evidence/logs/<projeto>-round<N>-validation.txt` (N = a rodada, a mesma do relatório):

```bash
LOG=../evidence/logs/<projeto>-round<N>-validation.txt
{ ./arch-check.sh; echo "exit: $?"; } | tee -a "$LOG"   # estrutura: AP-16
./manual-tests.sh 2>&1 | tee -a "$LOG"                  # comportamento: endpoints via curl
```

Os dois se complementam e nenhum substitui o outro — `manual-tests.sh` não distingue uma
rota que consulta o ORM direto de uma que delega. Se algum falhar, corrija antes de
reportar sucesso.

**A captura não é opcional e não pode ficar para depois.** A aplicação só está de pé neste
momento do fluxo; ao chegar no rollup de documentação (`/sync-docs`) o processo já morreu e a
saída do terminal já se perdeu — foi exatamente assim que a rodada 3 do `code-smells-project`
terminou sem evidência. Além dos dois scripts, inclua no mesmo log o boot da aplicação e um
`curl` por finding corrigido na rodada (a prova de que aquele finding específico saiu), e cite
o arquivo em `docs/results.md` e no README §3.4. `scripts/sync-docs.sh --check` falha se um
relatório em `reports/` for mais novo que a evidência do mesmo projeto.

O `arch-check.sh` de cada projeto é a versão específica dele (em português, padrões fixos) e
continua sendo a validação desta entrega. A skill empacota separadamente
`scripts/arch-check.sh`, genérico e detector de stack, para projetos que ainda não têm um —
os dois checam a mesma regra (AP-16) e ambos passam nos 3 projetos.

## README.md e docs/

Depois de **toda** rodada da skill, na raiz do repo:

```bash
claude "/sync-docs"      # ou: scripts/sync-docs.sh + as partes de julgamento
```

O README é o documento entregue, em português, com índice e âncoras — o leitor primário é
o avaliador do desafio, então nenhum item obrigatório (seções 1-4) pode ficar só atrás de
um link para `docs/`. A tabela [Conformidade com o enunciado](README.md#conformidade-com-o-enunciado)
é o que prova isso; atualize-a se criar/renomear seção, junto com o índice.

Quem escreve o quê:

| Alvo | Quem atualiza | Gatilho |
|---|---|---|
| README §3.1 (tabela de findings) | `scripts/sync-docs.sh`, entre marcadores | relatório novo em `reports/` |
| README §3.2 + `docs/project-structure.md` (árvores antes/depois) | `scripts/sync-docs.sh`, entre marcadores | estrutura de um projeto mudou |
| `docs/results.md` (rodada a rodada) | comando `/sync-docs` | relatório novo |
| README §3.3 (checklist) e Critérios de Aceite | comando `/sync-docs` | fim de uma Fase 3 |
| `evidence/logs/<projeto>-round<N>-validation.txt` | você, **durante** a validação (app de pé) | toda Fase 3 — ver seção acima, é gate obrigatório |
| README §3.4 + `evidence/` (citação do arquivo) | comando `/sync-docs` | evidência nova capturada |
| README §1, §2, §3.5 (`<!-- TODO -->`) | você | análise manual / design da skill |

Blocos entre `<!-- BEGIN:x -->` e `<!-- END:x -->` são **gerados** — editá-los à mão é
desfeito na rodada seguinte. Se o conteúdo está errado, o defeito está no
`scripts/sync-docs.sh` ou no relatório de origem.

`scripts/sync-docs.sh --check` sai 1 se README/`docs/` não refletirem `reports/` — rode
antes de encerrar a tarefa, junto com o `arch-check.sh` do projeto alterado.

## Convenções

- Commits: conventional commits com escopo do projeto, subject em inglês —
  `refactor(task-manager-api): resolve findings and extract controller`.
- Documentação (`README.md` dos projetos, comentários de `*.sh`): português.
  Skill e relatórios de auditoria: inglês.
- Nunca commitar `.env`, `*.db`, `instance/`, `node_modules/` (já no `.gitignore`).
- Projetos 1 e 3 usam a mesma porta 5000 — rode um por vez, ou sobrescreva `PORT`/`FLASK_PORT`.
- Vocabulário de domínio fica na língua original de cada projeto (`produtos`/`usuarios`
  no Projeto 1, inglês nos outros). Não traduza nomes de tabela, campo ou rota.
