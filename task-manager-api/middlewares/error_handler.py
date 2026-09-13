import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({'error': e.description}), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(_e):
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
