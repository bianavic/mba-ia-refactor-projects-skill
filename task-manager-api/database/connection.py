"""Database handle and the single commit path used by the models."""
import logging

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from errors.exceptions import AppError

logger = logging.getLogger(__name__)

db = SQLAlchemy()


def commit(error_message):
    """Commit the session; on failure roll back and raise a 500 with the API's message.

    Only the exception class is logged: SQLAlchemy's message carries the statement
    parameters (names, emails, password hashes)."""
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Database commit failed (%s)", type(exc).__name__)
        raise AppError(error_message, status=500)
