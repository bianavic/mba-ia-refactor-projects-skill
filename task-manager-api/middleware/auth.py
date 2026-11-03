"""Authentication (signed Bearer token) and authorization by role or owner."""
from functools import wraps

from flask import current_app, g, request

from config import settings
from errors.exceptions import Forbidden, Unauthorized
from models.task import Task
from models.user import User
from utils.security import fingerprints_match, read_token

_BEARER = "Bearer "
# Returned by an owner resolver when the resource does not exist: the controller answers 404.
RESOURCE_MISSING = object()


def _user_from_header(header):
    if not header.startswith(_BEARER):
        raise Unauthorized('Autenticação necessária')
    payload = read_token(current_app.config['SECRET_KEY'], header[len(_BEARER):].strip(),
                         settings.TOKEN_TTL_SECONDS)
    if not payload or 'id' not in payload or 'fp' not in payload:
        raise Unauthorized('Token inválido ou expirado')
    user = User.find(payload['id'])
    # the fingerprint rejects a token whose account was deleted and its id reused, or whose password changed
    if user is None or not fingerprints_match(user.token_fingerprint(), payload['fp']):
        raise Unauthorized('Token inválido ou expirado')
    if not user.active:
        raise Forbidden('Usuário inativo')
    return user


def _authenticate():
    g.current_user = _user_from_header(request.headers.get('Authorization', ''))
    return g.current_user


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        _authenticate()
        return fn(*args, **kwargs)
    return wrapper


def optional_auth(fn):
    """Public route that still needs to know an admin caller (POST /users role assignment)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get('Authorization')
        g.current_user = _user_from_header(header) if header else None
        return fn(*args, **kwargs)
    return wrapper


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not _authenticate().is_admin():
            raise Forbidden('Acesso negado')
        return fn(*args, **kwargs)
    return wrapper


def owner_or_admin(resolve_owner):
    """resolve_owner(kwargs) → owner user id, None (no owner: admin only) or RESOURCE_MISSING."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = _authenticate()
            if not user.is_admin():
                owner = resolve_owner(kwargs)
                if owner is not RESOURCE_MISSING and owner != user.id:
                    raise Forbidden('Acesso negado')
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ---------- owner resolvers (resource id → persisted owner identity) ----------

def owner_from_user_id(kwargs):
    """/users/<user_id>, /reports/user/<user_id>: the subject owns their own record."""
    return kwargs['user_id']


def owner_from_task_id(kwargs):
    """/tasks/<task_id>: the owner is the assignee (tasks.user_id); unassigned → admin only."""
    exists, user_id = Task.owner_of(kwargs['task_id'])
    return user_id if exists else RESOURCE_MISSING
