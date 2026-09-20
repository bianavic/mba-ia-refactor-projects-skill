"""Environment-driven configuration. No secrets or debug flags live in code."""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Deliberately no fallback value: a key that lives in the repository (even one
    # labelled "dev") is a publicly known signing key, so anyone could forge a
    # session token with it. create_app() validates this at startup and either
    # aborts (production) or mints an ephemeral in-memory key (development).
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    # Comma-separated list of allowed origins, or '*' (default) to preserve the
    # previous open-CORS behavior without a source edit.
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    # Lifetime of a login token, in seconds (default: 24h).
    TOKEN_MAX_AGE_SECONDS = int(os.environ.get('TOKEN_MAX_AGE_SECONDS', 86400))
