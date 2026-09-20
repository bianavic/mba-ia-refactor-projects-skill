#!/usr/bin/env bash
#
# sync-docs.sh — regenera as partes MECÂNICAS da documentação a partir de reports/ e do git.
#
# Gera dois blocos e os injeta entre marcadores HTML nos arquivos de destino:
#
#   audit-summary  -> README.md (3.1)              tabela de findings por severidade
#   project-trees  -> README.md (3.2)              árvores antes/depois dos 3 projetos
#                     docs/project-structure.md
#
# Fonte da verdade: reports/audit-project-*.md (linhas Project:/Stack:/## Summary,
# padronizadas pelo audit-report-template.md da skill) e o índice do git.
# Nada aqui exige julgamento — checklist, evidências e critérios de aceite que dependem
# de "a aplicação sobe" são responsabilidade do comando /sync-docs.
#
# Uso:
#   scripts/sync-docs.sh            regenera os blocos
#   scripts/sync-docs.sh --check    exit 1 se algum bloco estiver fora de sincronia
#
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Ordem canônica dos projetos: o índice é o <N> de audit-project-<N>.md
PROJETOS=(code-smells-project ecommerce-api-legacy task-manager-api)

# "Antes" = estado do boilerplate (primeiro commit do repositório)
BASE_REF="${BASE_REF:-$(git rev-list --max-parents=0 HEAD | tail -1)}"

MODO_CHECK=0
if [[ "${1:-}" == "--check" ]]; then MODO_CHECK=1; fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --------------------------------------------------------------------------
# Renderiza uma lista de caminhos ordenados como árvore com box-drawing.
# Recebe a raiz como $1 e os caminhos (relativos à raiz) por stdin.
# --------------------------------------------------------------------------
render_tree() {
  local raiz="$1"
  echo "${raiz}/"
  awk '
    {
      n = split($0, parts, "/")
      # pula o prefixo em comum com o caminho anterior (a lista vem ordenada,
      # então a ordem lexicográfica já é uma DFS pré-ordem válida)
      for (i = 1; i <= n; i++)
        if (i > prevn || parts[i] != prev[i]) break
      for (; i <= n; i++) {
        c++
        nome[c]  = parts[i]
        nivel[c] = i
        dir[c]   = (i < n)
      }
      for (i = 1; i <= n; i++) prev[i] = parts[i]
      prevn = n
    }
    END {
      # um nó é o último filho se nenhum nó seguinte, antes de a subárvore do pai
      # terminar, estiver no mesmo nível
      for (j = 1; j <= c; j++) {
        ultimo[j] = 1
        for (k = j + 1; k <= c; k++) {
          if (nivel[k] <  nivel[j]) break
          if (nivel[k] == nivel[j]) { ultimo[j] = 0; break }
        }
      }
      for (j = 1; j <= c; j++) {
        d = nivel[j]
        pilha[d] = ultimo[j]
        pfx = ""
        for (dd = 1; dd < d; dd++) pfx = pfx (pilha[dd] ? "    " : "│   ")
        printf "%s%s%s%s\n", pfx, (ultimo[j] ? "└── " : "├── "), nome[j], (dir[j] ? "/" : "")
      }
    }
  '
}

# Lista os arquivos versionados de um projeto num dado ref (vazio = índice atual)
listar_arquivos() {
  local projeto="$1" ref="${2:-}"
  if [[ -n "$ref" ]]; then
    git ls-tree -r --name-only "$ref" -- "$projeto" 2>/dev/null | sed "s|^$projeto/||"
  else
    git ls-files -- "$projeto" | sed "s|^$projeto/||"
  fi
}

# --------------------------------------------------------------------------
# Bloco 1 — tabela de auditoria
# --------------------------------------------------------------------------
gerar_audit_summary() {
  local projeto n relatorio stack crit high med low total
  echo "| # | Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |"
  echo "|---|---|---|---:|---:|---:|---:|---:|---|"
  n=0
  for projeto in "${PROJETOS[@]}"; do
    n=$((n + 1))
    # relatório corrente = maior -partM existente; na ausência de partes, o base
    relatorio="reports/audit-project-${n}.md"
    # o glob pode não casar nada (projeto sem re-auditoria): pipefail não pode matar o script
    parte="$( { ls -1 reports/audit-project-${n}-part*.md 2>/dev/null || true; } \
             | sed 's|.*-part\([0-9]*\)\.md$|\1|' | sort -n | tail -1)"
    if [[ -n "$parte" ]]; then relatorio="reports/audit-project-${n}-part${parte}.md"; fi
    if [[ ! -f "$relatorio" ]]; then
      echo "| $n | \`$projeto\` | — | — | — | — | — | — | _pendente_ |"
      continue
    fi
    stack="$(sed -n 's/^Stack: *//p' "$relatorio" | head -1)"
    read -r crit high med low <<<"$(sed -n '/^## Summary/,/^$/p' "$relatorio" \
      | sed -n 's/.*CRITICAL: *\([0-9]*\).*HIGH: *\([0-9]*\).*MEDIUM: *\([0-9]*\).*LOW: *\([0-9]*\).*/\1 \2 \3 \4/p' | head -1)"
    : "${crit:=0}" "${high:=0}" "${med:=0}" "${low:=0}"
    total=$((crit + high + med + low))
    echo "| $n | \`$projeto\` | $stack | $crit | $high | $med | $low | **$total** | [\`${relatorio#reports/}\`]($relatorio) |"
  done
  echo
  echo "<sub>Gerado por \`scripts/sync-docs.sh\` a partir de \`reports/\`. Não edite à mão.</sub>"
}

# --------------------------------------------------------------------------
# Bloco 2 — árvores antes/depois
# --------------------------------------------------------------------------
gerar_project_trees() {
  local projeto n
  n=0
  for projeto in "${PROJETOS[@]}"; do
    n=$((n + 1))
    echo "#### Projeto $n — \`$projeto\`"
    echo
    echo "<table><tr><th>Antes (boilerplate)</th><th>Depois (refatorado)</th></tr><tr><td>"
    echo
    echo '```'
    listar_arquivos "$projeto" "$BASE_REF" | render_tree "$projeto"
    echo '```'
    echo
    echo "</td><td>"
    echo
    echo '```'
    listar_arquivos "$projeto" | render_tree "$projeto"
    echo '```'
    echo
    echo "</td></tr></table>"
    echo
  done
  echo "<sub>Gerado por \`scripts/sync-docs.sh\` (\`git ls-tree $BASE_REF\` vs. \`git ls-files\`). Não edite à mão.</sub>"
}

# --------------------------------------------------------------------------
# Injeção entre marcadores
# --------------------------------------------------------------------------
injetar() {
  local arquivo="$1" marcador="$2" conteudo="$3" saida="$4"
  if ! grep -q "<!-- BEGIN:${marcador} -->" "$arquivo" \
     || ! grep -q "<!-- END:${marcador} -->" "$arquivo"; then
    echo "ERRO: marcadores BEGIN/END:${marcador} ausentes em ${arquivo}" >&2
    exit 2
  fi
  awk -v m="$marcador" -v cf="$conteudo" '
    $0 == "<!-- BEGIN:" m " -->" { print; while ((getline l < cf) > 0) print l; pulando = 1; next }
    $0 == "<!-- END:" m " -->"   { pulando = 0 }
    !pulando                     { print }
  ' "$arquivo" > "$saida"
}

gerar_audit_summary > "$TMP/audit-summary"
gerar_project_trees > "$TMP/project-trees"

# destino:marcador:marcador...
ALVOS=(
  "README.md:audit-summary:project-trees"
  "docs/project-structure.md:project-trees"
)

dessincronizados=()
for alvo in "${ALVOS[@]}"; do
  IFS=':' read -r arquivo marcadores <<<"$alvo"
  cp "$arquivo" "$TMP/alvo"
  for marcador in ${marcadores//:/ }; do
    injetar "$TMP/alvo" "$marcador" "$TMP/$marcador" "$TMP/alvo.novo"
    mv "$TMP/alvo.novo" "$TMP/alvo"
  done
  if cmp -s "$arquivo" "$TMP/alvo"; then
    (( MODO_CHECK )) || echo "ok        $arquivo (já sincronizado)"
  else
    dessincronizados+=("$arquivo")
    if (( MODO_CHECK )); then
      echo "DESSINC   $arquivo"
      diff -u "$arquivo" "$TMP/alvo" | sed -n '3,15p' || true
    else
      cp "$TMP/alvo" "$arquivo"
      echo "atualizado $arquivo"
    fi
  fi
done

if (( MODO_CHECK )) && (( ${#dessincronizados[@]} )); then
  echo
  echo "Documentação fora de sincronia com reports/. Rode: scripts/sync-docs.sh" >&2
  exit 1
fi

# --------------------------------------------------------------------------
# Gate de evidência — um relatório sem log de validação mais novo que ele
# significa que a Fase 3 rodou e a captura foi esquecida (ver CLAUDE.md,
# "Antes de dar uma refatoração por concluída"). Falha alto em vez de calar.
# --------------------------------------------------------------------------
sem_evidencia=()
n=0
for projeto in "${PROJETOS[@]}"; do
  n=$((n + 1))

  relatorio_recente="$( { ls -1t reports/audit-project-${n}.md reports/audit-project-${n}-part*.md 2>/dev/null || true; } | head -1)"
  [[ -n "$relatorio_recente" ]] || continue

  # evidência do projeto: por nome de diretório ou pela convenção projectN
  evidencia_recente="$( { find evidence -type f \( -name "*${projeto}*" -o -name "*project${n}*" \) 2>/dev/null || true; } \
                      | xargs -r ls -1t 2>/dev/null | head -1)"

  if [[ -z "$evidencia_recente" ]]; then
    sem_evidencia+=("$projeto — nenhuma evidência em evidence/ (relatório: ${relatorio_recente#reports/})")
  elif [[ "$relatorio_recente" -nt "$evidencia_recente" ]]; then
    sem_evidencia+=("$projeto — ${relatorio_recente#reports/} é mais novo que ${evidencia_recente#evidence/}")
  fi
done

if (( ${#sem_evidencia[@]} )); then
  echo
  echo "EVIDÊNCIA FALTANDO:"
  printf '  ✗ %s\n' "${sem_evidencia[@]}"
  echo
  echo "Capture a validação com a aplicação de pé em" >&2
  echo "evidence/logs/<projeto>-round<N>-validation.txt — ver CLAUDE.md," >&2
  echo "\"Antes de dar uma refatoração por concluída\"." >&2
  (( MODO_CHECK )) && exit 1
fi

if (( MODO_CHECK )); then
  echo "check ok — README.md e docs/project-structure.md refletem reports/, e todo relatório tem evidência"
fi
exit 0
