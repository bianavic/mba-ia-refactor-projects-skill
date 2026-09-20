import logging
import os

from flask import Flask
from flask_cors import CORS

from config.settings import Config
from database import db
from middlewares.error_handler import register_error_handlers
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from routes.meta_routes import meta_bp

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

logger = logging.getLogger(__name__)

DEV_ENVIRONMENTS = ('development', 'dev', 'test', 'testing')


def _ensure_secret_key(app):
    """Refuse to start without a real SECRET_KEY outside development.

    The key signs login tokens, so a value committed to the repository — even a
    'dev' default — would let anyone forge a token for any user. Development
    gets an ephemeral key instead: it is regenerated on every restart, so it is
    useless for forging a session that outlives the process.
    """
    if app.config.get('SECRET_KEY'):
        return

    environment = str(app.config.get('FLASK_ENV', 'production')).lower()
    if environment in DEV_ENVIRONMENTS or app.config.get('DEBUG') or app.config.get('TESTING'):
        app.config['SECRET_KEY'] = os.urandom(32).hex()
        logger.warning(
            "SECRET_KEY ausente: usando chave efêmera de desenvolvimento. "
            "Os tokens emitidos serão invalidados no próximo restart."
        )
        return

    raise RuntimeError(
        "SECRET_KEY não definida. Defina a variável de ambiente SECRET_KEY "
        "(veja .env.example) antes de iniciar a aplicação, ou rode com "
        "FLASK_ENV=development para uma chave efêmera de desenvolvimento."
    )


def create_app(config_object=Config):
    """Application factory: builds and wires a Flask app from a config object without
    any import-time side effect (no DB connection, no schema creation). Callers (the
    __main__ guard below, seed.py, tests/conftest.py) each decide when/whether to touch
    the database and with which config."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    _ensure_secret_key(app)

    origins = app.config['CORS_ORIGINS']
    if origins != '*':
        origins = [origin.strip() for origin in origins.split(',')]
    CORS(app, origins=origins)

    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(meta_bp)

    register_error_handlers(app)

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
