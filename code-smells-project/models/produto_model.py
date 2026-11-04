"""Acesso a dados de produtos."""
from database.connection import confirmar, get_db
from utils.paginacao import clausula_sql


def _serializar(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def listar(paginacao=None):
    limite, params = clausula_sql(paginacao)
    rows = get_db().execute("SELECT * FROM produtos ORDER BY id" + limite, params).fetchall()
    return [_serializar(r) for r in rows]


def obter_por_id(id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()
    return _serializar(row) if row else None


def obter_varios(ids):
    """Produtos por id, em um único SELECT ... IN (...)."""
    ids = list(set(ids))
    if not ids:
        return {}
    marcas = ",".join("?" for _ in ids)
    rows = get_db().execute("SELECT * FROM produtos WHERE id IN (" + marcas + ")", ids).fetchall()
    return {r["id"]: _serializar(r) for r in rows}


def nomes_por_ids(ids):
    return {id: p["nome"] for id, p in obter_varios(ids).items()}


def criar(nome, descricao, preco, estoque, categoria):
    cursor = get_db().execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    confirmar()
    return cursor.lastrowid


def atualizar(id, nome, descricao, preco, estoque, categoria):
    get_db().execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, id),
    )
    confirmar()
    return True


def deletar(id):
    get_db().execute("DELETE FROM produtos WHERE id = ?", (id,))
    confirmar()
    return True


def baixar_estoque(id, quantidade):
    """Baixa atômica: só decrementa se houver estoque. Devolve True se baixou."""
    cursor = get_db().execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (quantidade, id, quantidade),
    )
    confirmar()
    return cursor.rowcount == 1


def buscar(termo, categoria=None, preco_min=None, preco_max=None, paginacao=None):
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += ["%" + termo + "%", "%" + termo + "%"]
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max:
        query += " AND preco <= ?"
        params.append(preco_max)
    limite, params_limite = clausula_sql(paginacao)
    rows = get_db().execute(query + " ORDER BY id" + limite, params + params_limite).fetchall()
    return [_serializar(r) for r in rows]


def contar():
    return get_db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]


def apagar_todos():
    get_db().execute("DELETE FROM produtos")
    confirmar()
