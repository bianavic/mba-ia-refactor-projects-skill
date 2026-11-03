"""Composition root: configuração, banco, CORS, rotas e tratamento de erros."""
import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from database.connection import fechar_db, inicializar_db
from errors.handlers import registrar_handlers
from models import usuario_model
from routes import (admin_routes, pedido_routes, produto_routes, relatorio_routes,
                    sistema_routes, usuario_routes)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def criar_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app)

    for modulo in (produto_routes, usuario_routes, pedido_routes, relatorio_routes,
                   sistema_routes, admin_routes):
        app.register_blueprint(modulo.bp)

    registrar_handlers(app)
    app.teardown_appcontext(fechar_db)

    with app.app_context():
        inicializar_db()
        migradas = usuario_model.migrar_senhas_em_texto_puro()
        if migradas:
            logger.info("Senhas em texto puro convertidas em hash: %s", migradas)

    if settings.SECRET_KEY_GERADA:
        logger.warning("SECRET_KEY não definido: chave aleatória gerada (tokens não sobrevivem a reinícios)")
    return app


app = criar_app()

if __name__ == "__main__":
    logger.info("SERVIDOR INICIADO em http://%s:%s", settings.HOST, settings.PORT)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
