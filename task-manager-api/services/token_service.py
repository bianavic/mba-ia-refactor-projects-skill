"""Single owner of login-token issuance and verification.

Both the login flow (controllers/user_controller.py) and the HTTP guard
(middlewares/auth.py) go through this module, so the middleware consumes the
service and never the other way around.
"""
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

TOKEN_SALT = 'login-token'


class InvalidToken(Exception):
    """Raised when a token is malformed, tampered with, or expired."""


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=TOKEN_SALT)


def issue_token(user_id):
    """Return a signed token carrying the user id."""
    return _serializer().dumps({'user_id': user_id})


def read_token(token):
    """Return the user id carried by `token`, or raise InvalidToken.

    Verifies the signature and the token age; it does NOT decide whether the
    subject still exists or is still allowed in — that check belongs to the
    guard, which reloads the user on every request.
    """
    if not token:
        raise InvalidToken('Token ausente')

    max_age = current_app.config['TOKEN_MAX_AGE_SECONDS']
    try:
        payload = _serializer().loads(token, max_age=max_age)
    except SignatureExpired:
        raise InvalidToken('Token expirado')
    except BadSignature:
        raise InvalidToken('Token inválido')

    user_id = payload.get('user_id') if isinstance(payload, dict) else None
    if user_id is None:
        raise InvalidToken('Token inválido')

    return user_id
