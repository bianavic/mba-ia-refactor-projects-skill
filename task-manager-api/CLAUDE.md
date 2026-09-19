# task-manager-api (Projeto 3)

Flask 3.0.0 + Flask-SQLAlchemy 3.1.1, marshmallow, tokens assinados com `itsdangerous`,
SQLite. É o único projeto com testes automatizados (pytest).

## Rodar e validar

```bash
pip install -r requirements.txt
python seed.py         # dados de exemplo (opcional)
python app.py          # http://0.0.0.0:5000

pytest                 # testes unitários dos controllers
./manual-tests.sh      # endpoints via curl
./arch-check.sh        # AP-16: rotas não tocam persistência
```

Os três são complementares: `pytest` cobre os controllers, `manual-tests.sh` o
comportamento HTTP ponta a ponta, `arch-check.sh` a estrutura.

## Estrutura

`app.py` é o composition root; fluxo `routes/` → `controllers/` → `models/`, com
`services/report_service.py` para agregações de relatório e
`middlewares/error_handler.py` central.

- Rota faz parse do request (incluindo `page`/`per_page`) e chama uma função de
  controller. `arch-check.sh` falha se uma rota usar `db.session` ou `Model.query`.
- Constantes compartilhadas (`VALID_STATUSES`, `VALID_ROLES`, limites de tamanho) ficam
  em `utils/helpers.py` — importe, não redeclare na rota.
- Regras de domínio moram no model (`Task.to_dict()`, `Task.is_overdue()`). Não remonte
  dict de task à mão nem reimplemente a regra de atraso no controller.

## SQLAlchemy

Use a API 2.0 para acesso por chave primária: `db.session.get(Model, id)` — nunca
`Model.query.get(id)`, que está deprecado. O restante do código usa `Model.query.filter_by()`
/`.paginate()`; mantenha o estilo do arquivo em que estiver editando em vez de misturar.

Datas sempre com `utils/helpers.py:utc_now()` (`datetime.now(timezone.utc)`),
nunca `datetime.utcnow()`.

## Invariantes de segurança (achados CRITICAL já corrigidos — não regredir)

- Senha com `werkzeug.security` (não MD5) e **nunca** serializada em `to_dict()`.
- `/login` emite token assinado via `itsdangerous`, não string previsível.
- `SECRET_KEY`, `DATABASE_URL`, host e porta vêm de `config/settings.py` (env);
  `DEBUG` é `false` por padrão.
- Logging via `logging.getLogger`, nunca `print()` — `seed.py` é a exceção, é script de CLI.
- Toda listagem é paginada.
