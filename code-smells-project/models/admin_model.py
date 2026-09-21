from models.db import get_db

# Contagens pré-definidas e parametrizadas por tabela — nenhum SQL vindo do
# cliente chega ao cursor. `tabela` é apenas a chave de consulta neste dict.
CONTAGENS_POR_TABELA = {
    "produtos": "SELECT COUNT(*) FROM produtos",
    "usuarios": "SELECT COUNT(*) FROM usuarios",
    "pedidos": "SELECT COUNT(*) FROM pedidos",
    "itens_pedido": "SELECT COUNT(*) FROM itens_pedido",
}

TABELA_INVALIDA_ERRO = f"Tabela inválida. Válidas: {', '.join(CONTAGENS_POR_TABELA)}"


def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()


def executar_query(tabela):
    query = CONTAGENS_POR_TABELA.get(tabela)
    if query is None:
        raise ValueError(TABELA_INVALIDA_ERRO)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(query)
    total = cursor.fetchone()[0]
    return {"tabela": tabela, "total": total}
