from models.db import get_db

QUERY_SOMENTE_LEITURA_ERRO = "Somente instruções SELECT são permitidas nesta ferramenta"


def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()


def executar_query(query):
    if not query.strip().upper().startswith("SELECT"):
        raise ValueError(QUERY_SOMENTE_LEITURA_ERRO)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
