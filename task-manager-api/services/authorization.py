"""Authorization rules: who may act on what.

Authentication ("who is calling") is resolved by middlewares/auth.py; this
module answers the separate question of what that caller is allowed to do.
It knows nothing about HTTP — it takes the acting user as a plain argument so
controllers stay unit-testable without a request context.

Three kinds of actor:
  - SYSTEM  — trusted internal caller (seed script, unit tests). Full rights.
  - None    — an unauthenticated HTTP request. Lowest rights.
  - User    — an authenticated user; rights depend on role and ownership.
"""
from flask import abort

ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_USER = 'user'

#: Sentinel for trusted internal callers that bypass authorization entirely.
SYSTEM = object()

FORBIDDEN_MESSAGE = 'Permissão negada'


def is_system(actor):
    return actor is SYSTEM


def is_admin(actor):
    return getattr(actor, 'role', None) == ROLE_ADMIN


def has_role(actor, *roles):
    return getattr(actor, 'role', None) in roles


def ensure_can_manage_user(actor, target_user_id):
    """A user may edit/delete their own account; an admin may act on anyone."""
    if is_system(actor) or is_admin(actor):
        return
    if getattr(actor, 'id', None) == target_user_id:
        return
    abort(403, description=FORBIDDEN_MESSAGE)


def ensure_can_assign_role(actor, role):
    """Only an admin may create/promote an account to a privileged role.

    Without this, anonymous signup (`POST /users`) would let anybody register
    straight into the admin role.
    """
    if is_system(actor) or is_admin(actor):
        return
    if role != ROLE_USER:
        abort(403, description='Apenas um admin pode atribuir esse role')


def ensure_can_manage_task(actor, task):
    """A task may be changed/deleted by its owner or by an admin."""
    if is_system(actor) or is_admin(actor):
        return
    if task.user_id is not None and getattr(actor, 'id', None) == task.user_id:
        return
    abort(403, description=FORBIDDEN_MESSAGE)


def ensure_can_assign_task_owner(actor, user_id):
    """A non-admin may only create tasks owned by themselves (or unassigned)."""
    if is_system(actor) or is_admin(actor):
        return
    if user_id is None or getattr(actor, 'id', None) == user_id:
        return
    abort(403, description='Só é possível criar tasks para si mesmo')
