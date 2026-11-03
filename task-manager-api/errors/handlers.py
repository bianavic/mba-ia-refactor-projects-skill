"""Central error handling."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from errors.exceptions import AppError

logger = logging.getLogger(__name__)

INTERNAL_ERROR_MESSAGE = "Erro interno"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def app_error(exc):
        return jsonify(exc.body()), exc.status

    @app.errorhandler(Exception)
    def unexpected_error(exc):
        if isinstance(exc, HTTPException):
            return exc
        logger.error("Unhandled error (%s)", type(exc).__name__)
        return jsonify({"error": INTERNAL_ERROR_MESSAGE}), 500
