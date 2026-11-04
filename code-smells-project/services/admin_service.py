"""Operações administrativas e de saúde que tocam todas as entidades."""
import logging

from database.connection import transacao
from models import pedido_model, produto_model, usuario_model

logger = logging.getLogger(__name__)


def resetar_banco():
    with transacao():
        pedido_model.apagar_todos()
        produto_model.apagar_todos()
        usuario_model.apagar_todos()
    logger.warning("BANCO DE DADOS RESETADO")


def contagens():
    return {
        "produtos": produto_model.contar(),
        "usuarios": usuario_model.contar(),
        "pedidos": pedido_model.contar(),
    }
