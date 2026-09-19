# code-smells-project (Projeto 1)

Flask 3.1.1 + flask-cors, SQLite acessado por `sqlite3` cru (sem ORM). Domínio de
e-commerce com vocabulário em português: `produtos`, `usuarios`, `pedidos`, `itens_pedido`.

## Rodar e validar

```bash
pip install -r requirements.txt
python app.py          # http://0.0.0.0:5000
./manual-tests.sh      # endpoints via curl
./arch-check.sh        # AP-16: rotas não tocam persistência
```

Não há suíte automatizada — `manual-tests.sh` e `arch-check.sh` são a validação.

## Estrutura

`app.py` é o composition root (`create_app()`), e o fluxo é
`routes/routes.py` → `controllers/` → `models/`. Regras:

- Rota só faz parse do request, chama **uma** função de controller e serializa a resposta.
- Só `models/` fala com o banco. `models/db.py` centraliza conexão (`get_db()`) e schema.
- Configuração vem de `config/settings.py` (env vars), nunca hardcoded no código.

## Invariantes de segurança (achados CRITICAL já corrigidos — não regredir)

- **Toda** query SQL parametrizada (`?`). Nenhuma concatenação de string com input do
  usuário — o projeto tinha SQL injection em ~20 pontos.
- Campo `senha` nunca aparece em resposta de API; senhas via `werkzeug.security`.
- `SECRET_KEY`, `DEBUG` e `ADMIN_TOKEN` vêm do ambiente. `ADMIN_TOKEN` sem valor por
  padrão mantém os endpoints `/admin/*` desabilitados (403) — esse é o comportamento
  esperado, não um bug.
- `logging`, nunca `print()`.
- Listas de valores válidos (categorias, status) ficam em `config/settings.py`, não inline.

## Paginação

Listagens usam `DEFAULT_PAGE`/`DEFAULT_PER_PAGE` de `config/settings.py` via
`utils/pagination.py`. Endpoint de listagem novo nasce paginado.
