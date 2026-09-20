# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env     # SECRET_KEY vazia + FLASK_ENV=development já basta para rodar local
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

> Sem `.env`, o boot falha com uma mensagem explícita pedindo `SECRET_KEY` — é proposital: a chave assina os tokens de login e não tem default no código. Para um teste rápido sem criar `.env`, use `FLASK_ENV=development python app.py` (chave efêmera, perdida a cada restart). Em produção, gere uma chave real:
> `python -c "import secrets; print(secrets.token_hex(32))"`.

## Autenticação e autorização

Leituras (`GET`) são públicas. Toda escrita exige um token obtido em `POST /login`, enviado como `Authorization: Bearer <token>`:

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

curl -X POST http://localhost:5000/tasks \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Minha task"}'
```

Regras aplicadas:

| Ação | Quem pode |
|---|---|
| `GET` em qualquer recurso | qualquer um (público) |
| `POST /users` (cadastro) | qualquer um, mas só com `role: user` — apenas admin cria/promove a `admin`/`manager` |
| `PUT`/`DELETE /users/<id>` | o próprio usuário ou um admin |
| `POST /tasks` | qualquer usuário autenticado (só para si mesmo, exceto admin) |
| `PUT`/`DELETE /tasks/<id>` | o dono da task ou um admin |
| `POST`/`PUT`/`DELETE /categories` | apenas `admin` ou `manager` |

O token é verificado em `middlewares/auth.py`, que **recarrega o usuário do banco a cada request** — um token de conta apagada devolve 401 e de conta inativa devolve 403, sem esperar a expiração (`TOKEN_MAX_AGE_SECONDS`, default 24h).

## Validação

```bash
./arch-check.sh        # estrutura: nenhuma rota toca persistência (AP-16)
./manual-tests.sh      # comportamento: todos os endpoints via curl, com e sem token
python -m pytest -q    # testes unitários (controllers, autorização, token)
```
