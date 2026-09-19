# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

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

### Checagem arquitetural (AP-16)

```bash
./arch-check.sh
```

Verificação estática (não precisa da aplicação rodando) que garante que nenhuma rota ou
controller acessa a persistência diretamente — toda chamada ao banco deve passar por um
`models/*_model.py`. Sai com código 0 em caso de sucesso e lista arquivo:linha em caso de falha.
