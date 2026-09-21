---
description: Sincroniza README.md e docs/ com os relatórios em reports/ após uma rodada da skill
---

Sincronize a documentação do repositório com o estado atual de `reports/`.
Rode sempre a partir da **raiz do repositório** (`git rev-parse --show-toplevel`).

## 1. Parte mecânica

```bash
scripts/sync-docs.sh
```

Isso regenera, entre marcadores `<!-- BEGIN:... -->`:

- README §3.1 — tabela de findings por severidade, por projeto
- README §3.2 e `docs/project-structure.md` — árvores antes/depois

**Não edite blocos entre marcadores à mão** — a próxima rodada desfaz. Se algo estiver
errado ali, o defeito está no script ou no relatório de origem.

## 2. O que mudou desde a última sincronização

```bash
git status --porcelain reports/ docs/ README.md
git log --oneline -5
```

Leia os relatórios novos ou alterados (`reports/audit-project-*.md`). Para uma
re-auditoria (`-part<M>`), leia também a parte anterior: o que interessa é o delta —
o que foi resolvido e o que continua aberto.

## 3. `docs/results.md`

Atualize o deep dive de resultados: uma seção por projeto, com a rodada mais recente
(findings por severidade, o que a Fase 3 mudou de fato, o que ficou em aberto) e o
histórico das rodadas anteriores. Nunca apague uma rodada antiga — ela é a evidência
do estado "antes".

## 4. Partes de julgamento no README

Estas dependem do resultado real da rodada e por isso **não** são geradas pelo script:

- **§3.3 Checklist de Validação** — marque `✓` por projeto apenas o que você consegue
  sustentar com o relatório, o diff ou uma evidência. O que não foi verificado nesta
  rodada fica em branco.
- **Critérios de Aceite** — as duas primeiras linhas saem do relatório (≥ 5 findings,
  ≥ 1 CRITICAL/HIGH: confira contra a tabela de §3.1). "Fase 1 detecta a stack" sai da
  linha `Stack:` do relatório. "Aplicação funciona após refatoração" só pode ser marcada
  se a aplicação foi realmente executada — em caso de dúvida, deixe em branco e reporte.
- **§3.4 Evidências** — referencie os arquivos que existem em `evidence/`.

Regra dura: nenhum `✓` sem base verificável. Preferir uma célula vazia a uma afirmação
que o avaliador não consegue conferir.

## 5. Conferir

```bash
scripts/sync-docs.sh --check    # exit 0
cd <projeto-da-rodada> && ./arch-check.sh
```

## 6. Relatar as lacunas

Termine listando, em texto:

- projetos ainda sem relatório em `reports/`
- `<!-- TODO -->` que continuam no README (seções 1, 2, 3.5)
- projetos rodados que ainda não têm nada em `evidence/`
- células de checklist / critérios de aceite que ficaram em branco e por quê

Não commite: deixe as mudanças no working tree para revisão.
