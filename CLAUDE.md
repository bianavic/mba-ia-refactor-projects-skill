# mba-ia-refactor-projects-skill

Entrega do desafio de MBA: uma skill (`refactor-arch`) que audita e refatora projetos
legados para MVC, mais os 3 projetos legados em que ela foi executada. O produto
avaliado é o conjunto **skill + relatórios + código refatorado + README.md**.

```
code-smells-project/     Projeto 1 — Python/Flask, SQLite cru       (e-commerce)
ecommerce-api-legacy/    Projeto 2 — Node.js/Express, sqlite3       (LMS/e-learning)
task-manager-api/        Projeto 3 — Python/Flask + SQLAlchemy      (task manager)
reports/                 relatórios de auditoria (saída da Fase 2)
evidence/                screenshots citados na seção 4.6 do README
```

## A skill vive em triplicata

`.claude/skills/refactor-arch/` existe **idêntica** dentro dos 3 projetos — é exigência
do enunciado (seção 9.4.3 do README), não duplicação acidental.

- Qualquer edição em `SKILL.md`, `references/` ou `scripts/` deve ser replicada nas 3 cópias.
- Confirme antes de encerrar a tarefa:
  `diff -r code-smells-project/.claude/skills/refactor-arch <outro-projeto>/.claude/skills/refactor-arch`
- A skill é escrita em **inglês**. Mantenha assim, mesmo que a conversa seja em português.

## Relatórios

- `reports/audit-project-N.md` — N = 1 (code-smells), 2 (ecommerce), 3 (task-manager),
  4 (projeto Go/Gin externo, só Fases 1 e 2 — o código-fonte dele não é versionado aqui).
- Re-auditoria de um projeto já refatorado vai para `audit-project-N-part2.md`, com uma
  seção `## Resolved since audit-project-N.md` no topo. **Nunca sobrescreva** um relatório
  anterior: ele é a evidência do estado "antes".
- A Fase 2 da skill só imprime o relatório no terminal; salvar em `reports/` é passo manual.

## Antes de dar uma refatoração por concluída

Rode, dentro da pasta do projeto alterado:

```bash
./arch-check.sh     # estrutura: nenhuma rota toca persistência direto (AP-16)
./manual-tests.sh   # comportamento: todos os endpoints via curl
```

Os dois se complementam e nenhum substitui o outro — `manual-tests.sh` não distingue uma
rota que consulta o ORM direto de uma que delega. Se algum falhar, corrija antes de
reportar sucesso.

O `arch-check.sh` de cada projeto é a versão específica dele (em português, padrões fixos) e
continua sendo a validação desta entrega. A skill empacota separadamente
`scripts/arch-check.sh`, genérico e detector de stack, para projetos que ainda não têm um —
os dois checam a mesma regra (AP-16) e ambos passam nos 3 projetos.

## README.md

É o documento entregue, em português, com índice e âncoras. Ao mudar a estrutura de um
projeto ou o resultado de uma auditoria, atualize também as seções 5 (Resultados) e
6 (Estrutura Final) — e o índice, se criar/renomear seção.

## Convenções

- Commits: conventional commits com escopo do projeto, subject em inglês —
  `refactor(task-manager-api): resolve findings and extract controller`.
- Documentação (`README.md` dos projetos, comentários de `*.sh`): português.
  Skill e relatórios de auditoria: inglês.
- Nunca commitar `.env`, `*.db`, `instance/`, `node_modules/` (já no `.gitignore`).
- Projetos 1 e 3 usam a mesma porta 5000 — rode um por vez, ou sobrescreva `PORT`/`FLASK_PORT`.
- Vocabulário de domínio fica na língua original de cada projeto (`produtos`/`usuarios`
  no Projeto 1, inglês nos outros). Não traduza nomes de tabela, campo ou rota.
