"""Operações administrativas."""
import logging

from config import settings
from database.connection import executar_sql_bruto
from errors.exceptions import Forbidden, ValidationError
from services import admin_service

logger = logging.getLogger(__name__)


def resetar_banco(solicitante):
    admin_service.resetar_banco()
    logger.warning("Reset do banco executado por usuario_id=%s", solicitante["id"])
    return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200


def executar_query(solicitante, dados):
    if not settings.ADMIN_QUERY_ENABLED:
        raise Forbidden("Execução de SQL desabilitada (ADMIN_QUERY_ENABLED)")
    query = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not query or not isinstance(query, str):
        raise ValidationError("Query não informada")
    logger.warning("SQL administrativo executado por usuario_id=%s", solicitante["id"])
    resultado = executar_sql_bruto(query)
    if resultado is not None:
        return {"dados": resultado, "sucesso": True}, 200
    return {"mensagem": "Query executada", "sucesso": True}, 200
