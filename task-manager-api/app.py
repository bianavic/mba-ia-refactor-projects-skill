"""Composition root: wires config, database, CORS, error handling and routes, then starts the app."""
import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from database.connection import db
from errors.handlers import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.system_routes import system_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = settings.SECRET_KEY

if settings.SECRET_KEY_GENERATED:
    logger.warning("SECRET_KEY not set: a random key was generated (tokens do not survive restarts)")

CORS(app)
db.init_app(app)
register_error_handlers(app)

for blueprint in (system_bp, task_bp, user_bp, report_bp, category_bp):
    app.register_blueprint(blueprint)

with app.app_context():
    import models  # noqa: F401  (registers the tables before create_all)
    db.create_all()

if __name__ == '__main__':
    app.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
