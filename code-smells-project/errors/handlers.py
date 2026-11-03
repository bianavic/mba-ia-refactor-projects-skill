"""Tratamento central de erros."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from errors.exceptions import AppError

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INTERNO = "Erro interno do servidor"


def registrar_handlers(app):
    @app.errorhandler(AppError)
    def erro_da_aplicacao(e):
        return jsonify(e.corpo()), e.status

    @app.errorhandler(Exception)
    def erro_inesperado(e):
        if isinstance(e, HTTPException):
            return e
        logger.exception("Erro não tratado")
        return jsonify({"erro": MENSAGEM_ERRO_INTERNO}), 500
