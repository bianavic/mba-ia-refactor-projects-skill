"""HTTP authentication guard.

Turns an `Authorization: Bearer <token>` header into an authenticated User on
`g.current_user`. The signature alone is never enough: the subject is reloaded
from the database on every request, so a token stops working the moment the
account is deleted or deactivated — without waiting for the token to expire.
"""
import logging
from functools import wraps

from flask import abort, g, request

from database import db
from models.user import User
from services import authorization
from services.token_service import InvalidToken, read_token

logger = logging.getLogger(__name__)


def _bearer_token():
    header = request.headers.get('Authorization', '')
    scheme, _, token = header.partition(' ')
    if scheme.lower() != 'bearer' or not token.strip():
        return None
    return token.strip()


def _resolve_current_user():
    """Return the authenticated User, or abort with 401/403.

    401 — no token, bad signature, expired token, or the account no longer exists.
    403 — the account exists but is deactivated.
    """
    try:
        user_id = read_token(_bearer_token())
    except InvalidToken as exc:
        abort(401, description=str(exc))

    user = db.session.get(User, user_id)
    if not user:
        logger.warning("Token válido para usuário inexistente: %s", user_id)
        abort(401, description='Credenciais inválidas')

    if not user.active:
        abort(403, description='Usuário inativo')

    return user


def login_required(view):
    """Require a valid token bound to an existing, active user."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        g.current_user = _resolve_current_user()
        return view(*args, **kwargs)
    return wrapper


def optional_auth(view):
    """Populate g.current_user when a valid token is present, without requiring one.

    Used by endpoints that stay public but behave differently for a signed-in
    caller (e.g. anonymous signup may not choose a privileged role).
    """
    @wraps(view)
    def wrapper(*args, **kwargs):
        g.current_user = None
        if _bearer_token():
            g.current_user = _resolve_current_user()
        return view(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    """Require an authenticated user holding one of `roles` (admin always passes)."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            user = g.current_user
            if not (authorization.is_admin(user) or authorization.has_role(user, *roles)):
                abort(403, description=authorization.FORBIDDEN_MESSAGE)
            return view(*args, **kwargs)
        return wrapper
    return decorator


def current_user():
    """The authenticated user for this request, or None when unauthenticated."""
    return g.get('current_user')
