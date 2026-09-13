from config.settings import PRODUTO_CATEGORIAS_VALIDAS
from models.db import get_db


def _to_dict(row):
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


def _validar_campos(nome, preco, estoque, categoria):
    if preco < 0:
        raise ValueError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValueError("Estoque não pode ser negativo")
    if len(nome) < 2:
        raise ValueError("Nome muito curto")
    if len(nome) > 200:
        raise ValueError("Nome muito longo")
    if categoria not in PRODUTO_CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoria inválida. Válidas: {PRODUTO_CATEGORIAS_VALIDAS}")


def get_todos(page=1, per_page=20):
    db = get_db()
    cursor = db.cursor()
    offset = (page - 1) * per_page
    cursor.execute("SELECT * FROM produtos LIMIT ? OFFSET ?", (per_page, offset))
    return [_to_dict(row) for row in cursor.fetchall()]


def get_por_id(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cursor.fetchone()
    return _to_dict(row) if row else None


def criar(nome, descricao, preco, estoque, categoria):
    _validar_campos(nome, preco, estoque, categoria)
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    _validar_campos(nome, preco, estoque, categoria)
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ?
           WHERE id = ?""",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()
    return True


def deletar(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()
    return True


def buscar(termo, categoria=None, preco_min=None, preco_max=None):
    db = get_db()
    cursor = db.cursor()

    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        curinga = f"%{termo}%"
        params.extend([curinga, curinga])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)

    cursor.execute(query, params)
    return [_to_dict(row) for row in cursor.fetchall()]


def count():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM produtos")
    return cursor.fetchone()[0]
