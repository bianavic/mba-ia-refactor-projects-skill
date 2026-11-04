"""Acesso a dados de pedidos e itens_pedido, e o relatório de vendas."""
from config import settings
from database.connection import confirmar, get_db
from utils.paginacao import clausula_sql


def _serializar(row, itens):
    return {
        "id": row["id"],
        "usuario_id": row["usuario_id"],
        "status": row["status"],
        "total": row["total"],
        "criado_em": row["criado_em"],
        "itens": itens,
    }


def _itens_por_pedido(pedido_ids):
    """Itens de vários pedidos em um único SELECT ... IN (...)."""
    if not pedido_ids:
        return {}
    marcas = ",".join("?" for _ in pedido_ids)
    rows = get_db().execute(
        "SELECT * FROM itens_pedido WHERE pedido_id IN (" + marcas + ") ORDER BY id", list(pedido_ids)
    ).fetchall()
    agrupados = {}
    for item in rows:
        agrupados.setdefault(item["pedido_id"], []).append({
            "produto_id": item["produto_id"],
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"],
        })
    return agrupados


def _listar(where, params, paginacao):
    limite, params_limite = clausula_sql(paginacao)
    rows = get_db().execute(
        "SELECT * FROM pedidos" + where + " ORDER BY id" + limite, list(params) + params_limite
    ).fetchall()
    itens = _itens_por_pedido([r["id"] for r in rows])
    return [_serializar(r, itens.get(r["id"], [])) for r in rows]


def listar_todos(paginacao=None):
    return _listar("", [], paginacao)


def listar_por_usuario(usuario_id, paginacao=None):
    return _listar(" WHERE usuario_id = ?", [usuario_id], paginacao)


def criar(usuario_id, total, itens):
    """Insere o pedido e seus itens. itens: [{produto_id, quantidade, preco_unitario}]."""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, settings.STATUS_PEDIDO_INICIAL, total),
    )
    pedido_id = cursor.lastrowid
    db.executemany(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        [(pedido_id, i["produto_id"], i["quantidade"], i["preco_unitario"]) for i in itens],
    )
    confirmar()
    return pedido_id


def atualizar_status(pedido_id, novo_status):
    get_db().execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    confirmar()
    return True


def desvincular_usuario(usuario_id):
    """Mantém os pedidos (contabilidade) mas remove o vínculo com o titular."""
    get_db().execute("UPDATE pedidos SET usuario_id = NULL WHERE usuario_id = ?", (usuario_id,))
    confirmar()


def calcular_desconto(faturamento):
    for limite, taxa in settings.FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


def relatorio_vendas():
    db = get_db()
    total_pedidos, faturamento = db.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM pedidos").fetchone()
    por_status = dict(db.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status").fetchall())
    desconto = calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": por_status.get(settings.STATUS_PEDIDO_INICIAL, 0),
        "pedidos_aprovados": por_status.get(settings.STATUS_APROVADO, 0),
        "pedidos_cancelados": por_status.get(settings.STATUS_CANCELADO, 0),
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }


def contar():
    return get_db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]


def apagar_todos():
    db = get_db()
    db.execute("DELETE FROM itens_pedido")
    db.execute("DELETE FROM pedidos")
    confirmar()
