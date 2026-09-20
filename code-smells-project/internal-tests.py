#!/usr/bin/env python3
"""
internal-tests.py -- checagens de caixa-branca, em processo, sem servidor.

Completa os outros dois validadores do projeto:
    arch-check.sh      -> estrutura (AP-16: rota nao toca persistencia)
    manual-tests.sh    -> comportamento via HTTP (precisa da app de pe)
    internal-tests.py  -> propriedades que a resposta HTTP nao revela

O que so da para provar aqui:
    1. Que get_todos (AP-08) nao volta a ser N+1. O numero de queries emitidas
       nao pode crescer com a quantidade de pedidos -- _hydrate_pedidos busca
       todos os itens/produtos de uma vez com WHERE ... IN (...).
    2. Que a checagem acima sabe reprovar (controle negativo). Um teste que so
       sabe passar nao mede nada: uma query por item (jeito antigo) TEM que
       crescer com N.

Uso:  python3 internal-tests.py
Saida: 0 = todas passaram, 1 = alguma falhou.
"""
import os
import sys
from contextlib import contextmanager

os.environ.setdefault("DB_PATH", ":memory:")

from app import create_app  # noqa: E402
from models import order_model  # noqa: E402
from models.db import get_db, _create_schema, _seed_if_empty  # noqa: E402

results = []


def check(name, passed, detail=""):
    results.append((name, passed))
    print(f"  {'✓' if passed else '✗'} {name}")
    if detail:
        print(f"      {detail}")


@contextmanager
def count_queries(db):
    """Conta quantos statements SQL rodam na conexao `db` durante o bloco `with`,
    via sqlite3.Connection.set_trace_callback (Cursor.execute e imutavel em CPython,
    nao da para monkeypatchar)."""
    count = 0

    def trace(_statement):
        nonlocal count
        count += 1

    db.set_trace_callback(trace)
    try:
        yield lambda: count
    finally:
        db.set_trace_callback(None)


def seed_pedido(db, usuario_id, itens):
    """Insere um pedido com N itens direto via SQL, sem passar por order_model.criar
    (que teria sua propria contagem de queries)."""
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', 0)",
        (usuario_id,),
    )
    pedido_id = cursor.lastrowid
    for produto_id, quantidade in itens:
        cursor.execute(
            """INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
               VALUES (?, ?, ?, 1.0)""",
            (pedido_id, produto_id, quantidade),
        )
    db.commit()
    return pedido_id


def check_get_todos_query_count_constant(db):
    """1. get_todos: numero de queries constante, nao cresce com N pedidos."""
    produto_ids = [row["id"] for row in db.execute("SELECT id FROM produtos").fetchall()]

    for _ in range(3):
        seed_pedido(db, 1, [(produto_ids[0], 1), (produto_ids[1], 2)])
    with count_queries(db) as small_counter:
        small_result = order_model.get_todos(page=1, per_page=50)
    small_count = small_counter()

    for _ in range(12):
        seed_pedido(db, 1, [(produto_ids[0], 1), (produto_ids[1], 2)])
    with count_queries(db) as large_counter:
        large_result = order_model.get_todos(page=1, per_page=50)
    large_count = large_counter()

    check(
        "get_todos: numero de queries nao cresce com a quantidade de pedidos",
        small_count == large_count and large_count <= 2,
        f"{len(small_result)} pedido(s) -> {small_count} querie(s) | "
        f"{len(large_result)} pedido(s) -> {large_count} querie(s)",
    )


def check_naive_per_item_loop_would_grow(db):
    """2. Controle negativo: uma query por item (jeito antigo) TEM que crescer com N."""
    cursor = db.cursor()
    cursor.execute("SELECT id FROM itens_pedido")
    item_ids = cursor.fetchall()

    with count_queries(db) as counter:
        for _ in item_ids:
            cursor.execute("SELECT nome FROM produtos WHERE id = 1")
    naive_count = counter()

    check(
        "controle negativo: uma query por item cresce com N "
        "(prova que a checagem acima mede algo)",
        naive_count == len(item_ids),
        f"{len(item_ids)} item(ns) -> {naive_count} querie(s) no jeito ingenuo",
    )


def main():
    print("=" * 58)
    print("internal-tests -- code-smells-project")
    print("Checagens em processo (sem servidor)")
    print("=" * 58)
    print()

    app = create_app()

    # Um unico app context para toda a rodada: DB_PATH=:memory: vive e morre com
    # a conexao guardada em flask.g, entao contextos separados veriam bancos
    # distintos (e vazios) um do outro.
    with app.app_context():
        db = get_db()
        _create_schema()
        _seed_if_empty()
        check_get_todos_query_count_constant(db)
        check_naive_per_item_loop_would_grow(db)

    failed = [name for name, passed in results if not passed]
    print()
    print("=" * 58)
    if not failed:
        print(f"PASS: {len(results)} checagem(ns) internas OK.")
        print("=" * 58)
        sys.exit(0)
    print(f"FAIL: {len(failed)} de {len(results)} checagem(ns) falharam.")
    for name in failed:
        print(f"  - {name}")
    print("=" * 58)
    sys.exit(1)


if __name__ == "__main__":
    main()
