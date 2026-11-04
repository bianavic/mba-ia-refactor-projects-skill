"""Fluxo HTTP de pedidos."""
from config import settings
from errors.exceptions import ValidationError
from services import pedido_service


def _inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _validar_itens(itens):
    if not isinstance(itens, list):
        raise ValidationError("Itens deve ser uma lista")
    validados = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Cada item deve ser um objeto com produto_id e quantidade")
        produto_id = item.get("produto_id")
        quantidade = item.get("quantidade")
        if not _inteiro(produto_id):
            raise ValidationError("produto_id deve ser um número inteiro")
        if not _inteiro(quantidade) or quantidade <= 0:
            raise ValidationError("quantidade deve ser um número inteiro maior que zero")
        validados.append({"produto_id": produto_id, "quantidade": quantidade})
    return validados


def criar_pedido(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _inteiro(usuario_id):
        raise ValidationError("Usuario ID deve ser um número inteiro")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    resultado = pedido_service.criar_pedido(usuario_id, _validar_itens(itens))
    return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201


def listar_pedidos_usuario(usuario_id, paginacao):
    return {"dados": pedido_service.listar_por_usuario(usuario_id, paginacao), "sucesso": True}, 200


def listar_todos_pedidos(paginacao):
    return {"dados": pedido_service.listar_todos(paginacao), "sucesso": True}, 200


def atualizar_status_pedido(pedido_id, dados):
    novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
    if novo_status not in settings.STATUS_PEDIDO:
        raise ValidationError("Status inválido")
    pedido_service.atualizar_status(pedido_id, novo_status)
    return {"sucesso": True, "mensagem": "Status atualizado"}, 200
