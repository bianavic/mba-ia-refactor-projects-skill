"""Casos de uso de pedidos: envolvem usuários, produtos, pedidos e notificações."""
from database.connection import transacao
from errors.exceptions import NotFound, ValidationError
from models import pedido_model, produto_model, usuario_model
from services import notificacao_service


def criar_pedido(usuario_id, itens):
    """itens: [{produto_id, quantidade}] já validados. Tudo ou nada, em uma transação."""
    with transacao():
        if not usuario_model.existe(usuario_id):
            raise NotFound("Usuário não encontrado")

        produtos = produto_model.obter_varios([i["produto_id"] for i in itens])
        total = 0
        itens_pedido = []
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado", incluir_sucesso=True)
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError("Estoque insuficiente para " + produto["nome"], incluir_sucesso=True)
            total = total + (produto["preco"] * item["quantidade"])
            itens_pedido.append({
                "produto_id": item["produto_id"],
                "quantidade": item["quantidade"],
                "preco_unitario": produto["preco"],
            })

        for item in itens_pedido:
            if not produto_model.baixar_estoque(item["produto_id"], item["quantidade"]):
                nome = produtos[item["produto_id"]]["nome"]
                raise ValidationError("Estoque insuficiente para " + nome, incluir_sucesso=True)

        pedido_id = pedido_model.criar(usuario_id, total, itens_pedido)

    notificacao_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def _com_nomes(pedidos):
    ids = [i["produto_id"] for p in pedidos for i in p["itens"]]
    nomes = produto_model.nomes_por_ids(ids)
    for pedido in pedidos:
        pedido["itens"] = [
            {
                "produto_id": i["produto_id"],
                "produto_nome": nomes.get(i["produto_id"], "Desconhecido"),
                "quantidade": i["quantidade"],
                "preco_unitario": i["preco_unitario"],
            }
            for i in pedido["itens"]
        ]
    return pedidos


def listar_todos(paginacao=None):
    return _com_nomes(pedido_model.listar_todos(paginacao))


def listar_por_usuario(usuario_id, paginacao=None):
    return _com_nomes(pedido_model.listar_por_usuario(usuario_id, paginacao))


def atualizar_status(pedido_id, novo_status):
    pedido_model.atualizar_status(pedido_id, novo_status)
    notificacao_service.status_alterado(pedido_id, novo_status)
