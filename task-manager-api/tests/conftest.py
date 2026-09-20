import pytest

from app import create_app
from config.settings import Config
from database import db
import models  # noqa: F401 — registers Task/User/Category with SQLAlchemy


class TestConfig(Config):
    """Same settings as production except for an isolated in-memory database."""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret'
    TESTING = True


@pytest.fixture
def app():
    """A Flask app built by the same factory as production, bound to an in-memory
    SQLite DB isolated from tasks.db."""
    test_app = create_app(TestConfig)

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()
