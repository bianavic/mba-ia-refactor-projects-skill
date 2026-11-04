"""Direitos do titular: exclusão e exportação (usuários + pedidos)."""
from database.connection import transacao
from errors.exceptions import NotFound
from models import pedido_model, usuario_model
from services import pedido_service


def excluir_usuario(usuario_id):
    """Desvincula os pedidos (mantidos para contabilidade) e apaga o usuário, numa transação."""
    with transacao():
        if not usuario_model.existe(usuario_id):
            raise NotFound("Usuário não encontrado")
        pedido_model.desvincular_usuario(usuario_id)
        usuario_model.deletar(usuario_id)


def exportar_usuario(usuario_id):
    usuario = usuario_model.obter_por_id(usuario_id)
    if usuario is None:
        raise NotFound("Usuário não encontrado")
    return {"usuario": usuario, "pedidos": pedido_service.listar_por_usuario(usuario_id)}
