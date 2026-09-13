import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from middlewares.error_handler import register_error_handlers
from models import db as db_module
from routes.routes import register_routes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app)

    db_module.init_app(app)
    register_routes(app)
    register_error_handlers(app)

    return app


app = create_app()

if __name__ == "__main__":
    logger.info("Servidor iniciado em http://%s:%s", settings.HOST, settings.PORT)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
