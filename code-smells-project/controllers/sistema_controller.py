"""Boas-vindas e health check."""
import logging

from config import settings
from errors.handlers import MENSAGEM_ERRO_INTERNO
from services import admin_service

logger = logging.getLogger(__name__)


def index():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": settings.VERSAO,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }, 200


def health_check():
    try:
        contagens = admin_service.contagens()
    except Exception:
        logger.exception("Health check falhou")
        return {"status": "erro", "detalhes": MENSAGEM_ERRO_INTERNO}, 500
    return {"status": "ok", "database": "connected", "counts": contagens, "versao": settings.VERSAO}, 200
