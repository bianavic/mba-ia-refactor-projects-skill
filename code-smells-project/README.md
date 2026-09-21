# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

### Variáveis de ambiente

Este projeto **não tem `.env.example`** (diferente dos outros dois do repositório); as variáveis
são lidas em `config/settings.py` e todas têm default:

| Variável | Default | Observação |
|---|---|---|
| `SECRET_KEY` | `dev-only-change-me` | Default versionado — **troque em qualquer uso real**. Ao contrário do `task-manager-api`, a aplicação não se recusa a subir sem ela. |
| `ADMIN_TOKEN` | *(vazio)* | Sem valor, `/admin/*` responde 403. Ver a seção de testes. |
| `DB_PATH` | `loja.db` | Caminho do SQLite. |
| `HOST` / `PORT` | `0.0.0.0` / `5000` | Projetos 1 e 3 usam a 5000 — rode um por vez. |
| `DEBUG` | `false` | |

## Testes

### Testes manuais (comportamento HTTP)

Com a aplicação rodando (`python app.py`), execute em outro terminal:

```bash
bash manual-tests.sh
```

O script cobre todos os endpoints (produtos, usuários, pedidos, relatórios) e também os
endpoints administrativos. Por padrão `/admin/*` fica desabilitado (403) — para testar essa
parte, suba o servidor com um token antes:

```bash
ADMIN_TOKEN=algum-token python app.py
```

e envie o header `X-Admin-Token: algum-token` nas chamadas a `/admin/reset-db` e `/admin/query`
(`/admin/query` só aceita instruções `SELECT`).

Para explorar a API interativamente (endpoint por endpoint, com resposta formatada), use
`api-tests.http` com a extensão "REST Client" do VS Code ou equivalente — cobre os mesmos
endpoints do `manual-tests.sh`, além de edge cases (parâmetros inválidos, limites de permissão
do `/admin/*`) que o script não exercita.

### Testes internos (caixa-branca)

```bash
python internal-tests.py
```

Roda em processo, sem precisar da aplicação de pé, e cobre o que a resposta HTTP não revela.
Complementa o `manual-tests.sh` — nenhum dos dois substitui o outro.

### Checagem arquitetural (AP-16)

```bash
./arch-check.sh
```

Verificação estática (não precisa da aplicação rodando) que garante que nenhuma rota ou
controller acessa a persistência diretamente — toda chamada ao banco deve passar por um
`models/*_model.py`. Sai com código 0 em caso de sucesso e lista arquivo:linha em caso de falha.
