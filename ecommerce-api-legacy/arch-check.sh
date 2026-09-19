#!/usr/bin/env bash
#
# arch-check.sh — checagem arquitetural (caixa-branca) deste projeto.
#
# Complementa o manual-tests.sh: aquele prova o COMPORTAMENTO via HTTP, este
# prova a ESTRUTURA lendo o código. A separação existe porque teste de
# caixa-preta não distingue uma rota que consulta o ORM direto de uma que
# delega para um controller/service — a resposta HTTP é idêntica nos dois casos.
#
# Verifica o AP-16 ("Persistence/ORM Calls Inline in Routes"): nenhum arquivo de
# rota/view pode chamar persistência diretamente — a rota só pode fazer parse do
# request, chamar UMA função de Controller/Service e serializar o resultado.
#
# Uso:
#   ./arch-check.sh
#
# Saída: 0 = PASS (nenhuma chamada inline), 1 = FAIL (lista arquivo:linha).

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="$(basename "$PROJECT_DIR")"

# Padrões de persistência direta. Mantidos em sincronia com o sinal do AP-16 em
# .claude/skills/refactor-arch/references/anti-patterns-catalog.md:
#   1. sessão do ORM            db.session.add/commit/delete/...
#   2. query attribute          Task.query, User.query.get(...)
#   3. finders/writers de Model Model.find/findById/create/update/get_by_id/find_by_x(...)
#   4. driver/cursor cru        cursor.execute(...), db.run(...), conn.query(...)
#   5. SQL literal              SELECT ... FROM, INSERT INTO, DELETE FROM, UPDATE x SET
PATTERN='db\.session\.'
PATTERN="$PATTERN"'|\b[A-Z][A-Za-z0-9_]*\.query\b'
PATTERN="$PATTERN"'|\b[A-Z][A-Za-z0-9_]*\.(find|findOne|findAll|findById|findByPk|create|update|destroy|insert|save|delete|remove|get_by_id|get_all|find_by_[a-z_]+)[[:space:]]*\('
PATTERN="$PATTERN"'|\b(cursor|conn|connection|db|database|pool|knex)\.(execute|executemany|query|run|all|get|prepare)[[:space:]]*\('
PATTERN="$PATTERN"'|SELECT[[:space:]].*[[:space:]]FROM[[:space:]]|INSERT[[:space:]]+INTO[[:space:]]|DELETE[[:space:]]+FROM[[:space:]]|UPDATE[[:space:]]+[A-Za-z_]+[[:space:]]+SET[[:space:]]'

# Linhas de comentário puro não são código — não contam como violação.
COMMENT_ONLY='^[0-9]+:[[:space:]]*(#|//|\*|/\*|"""|'"'''"')'

printf '==========================================================\n'
printf 'arch-check — %s\n' "$PROJECT_NAME"
printf 'AP-16: rotas não podem tocar a persistência diretamente\n'
printf '==========================================================\n'

# Arquivos de rota/view, ignorando vendor/venv e a cópia da skill.
route_files="$(
  find "$PROJECT_DIR" \
    \( -name node_modules -o -name .git -o -name .claude -o -name venv \
       -o -name .venv -o -name __pycache__ -o -name dist -o -name build \) -prune -o \
    -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' \) -print 2>/dev/null \
    | grep -E '/(routes|views)/' | sort
)"

if [ -z "$route_files" ]; then
  printf '\nNenhum arquivo de rota encontrado em routes/ ou views/.\n'
  printf '==========================================================\n'
  exit 0
fi

total_hits=0
bad_files=0
scanned=0

printf '\n'
while IFS= read -r file; do
  [ -n "$file" ] || continue
  rel="${file#"$PROJECT_DIR"/}"
  scanned=$((scanned + 1))

  hits="$(grep -nE "$PATTERN" "$file" 2>/dev/null | grep -vE "$COMMENT_ONLY")"

  if [ -z "$hits" ]; then
    printf '  ✓ %s\n' "$rel"
  else
    count="$(printf '%s\n' "$hits" | wc -l | tr -d ' ')"
    printf '  ✗ %s — %s chamada(s) inline\n' "$rel" "$count"
    printf '%s\n' "$hits" | sed 's/^/      /'
    total_hits=$((total_hits + count))
    bad_files=$((bad_files + 1))
  fi
done <<EOF
$route_files
EOF

printf '\n==========================================================\n'
if [ "$total_hits" -eq 0 ]; then
  printf 'PASS: no route in %s touches persistence directly.\n' "$PROJECT_NAME"
  printf '(%d arquivo(s) de rota verificado(s))\n' "$scanned"
  printf '==========================================================\n'
  exit 0
fi

printf 'FAIL: %d chamada(s) de persistência inline em %d arquivo(s) de rota.\n' \
  "$total_hits" "$bad_files"
printf 'Mova cada chamada para um Controller/Service; a rota só pode chamar essa função.\n'
printf '==========================================================\n'
exit 1
