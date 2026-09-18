import pytest
from flask import Flask

from database import db
import models  # noqa: F401 — registers Task/User/Category with SQLAlchemy


@pytest.fixture
def app():
    """A Flask app bound to an in-memory SQLite DB, isolated from tasks.db."""
    test_app = Flask(__name__)
    test_app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY='test-secret',
        TESTING=True,
    )
    db.init_app(test_app)

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()
