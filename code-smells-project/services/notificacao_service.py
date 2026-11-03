"""Canal externo de notificações (email/SMS/push). Hoje só registra no log; nunca dados pessoais."""
import logging

from config import settings

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
    logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
    logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")


def status_alterado(pedido_id, novo_status):
    if novo_status == settings.STATUS_APROVADO:
        logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
    if novo_status == settings.STATUS_CANCELADO:
        logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)
