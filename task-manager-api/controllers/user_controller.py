"""User request flow: validation, role-assignment rules, masking by audience."""
import logging

from config import settings
from errors.exceptions import Conflict, Forbidden, NotFound, ValidationError
from models.user import User
from services import user_service
from utils.helpers import validate_email
from utils.pagination import parse_pagination

logger = logging.getLogger(__name__)


def _is_subject(viewer, user):
    return viewer is not None and viewer.id == user.id


def _is_admin(viewer):
    return viewer is not None and viewer.is_admin()


def _require_body(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError('Dados inválidos')


def _validate_name(name):
    if not isinstance(name, str) or not name.strip():
        raise ValidationError('Nome é obrigatório')
    return name


def _validate_email(email):
    if not validate_email(email):
        raise ValidationError('Email inválido')
    return email


def _validate_password(password, message):
    if not isinstance(password, str) or len(password) < settings.MIN_PASSWORD_LENGTH:
        raise ValidationError(message)
    return password


def _validate_role(role):
    if not isinstance(role, str) or role not in settings.VALID_ROLES:
        raise ValidationError('Role inválido')
    return role


def _check_privileged_fields(data, viewer):
    """role/active are writable only by an admin (a non-admin may only send role 'user')."""
    if _is_admin(viewer):
        return
    if 'role' in data and data['role'] != settings.DEFAULT_ROLE:
        raise Forbidden('Apenas administradores podem definir role')
    if 'active' in data:
        raise Forbidden('Apenas administradores podem alterar active')


def _ensure_email_free(email, user_id=None):
    existing = User.find_by_email(email)
    if existing is not None and existing.id != user_id:
        raise Conflict('Email já cadastrado')


# ---------- handlers ----------

def list_users(args, viewer):
    rows = user_service.list_users_with_task_counts(parse_pagination(args))
    result = []
    for user, task_count in rows:
        data = user.to_dict(full_email=_is_subject(viewer, user))
        data['task_count'] = task_count
        result.append(data)
    return result, 200


def get_user(user_id, args, viewer):
    user, tasks = user_service.get_user_with_tasks(user_id, parse_pagination(args))
    data = user.to_dict(full_email=_is_subject(viewer, user))
    data['tasks'] = [item.to_dict() for item in tasks]
    return data, 200


def create_user(data, viewer):
    _require_body(data)
    if not data.get('name'):
        raise ValidationError('Nome é obrigatório')
    if not data.get('email'):
        raise ValidationError('Email é obrigatório')
    if not data.get('password'):
        raise ValidationError('Senha é obrigatória')
    name = _validate_name(data['name'])
    email = _validate_email(data['email'])
    password = _validate_password(data['password'], 'Senha deve ter no mínimo 4 caracteres')
    _ensure_email_free(email)
    role = _validate_role(data.get('role', settings.DEFAULT_ROLE))
    _check_privileged_fields({'role': role}, viewer)

    user = User.create(name, email, password, role)
    logger.info("User created: id=%s", user.id)
    # an anonymous signup is the subject itself; an admin creating someone else sees the masked email
    return user.to_dict(full_email=viewer is None or _is_subject(viewer, user)), 201


def update_user(user_id, data, viewer):
    user = User.find(user_id)
    if user is None:
        raise NotFound('Usuário não encontrado')
    _require_body(data)

    fields = {}
    if 'name' in data:
        fields['name'] = _validate_name(data['name'])
    if 'email' in data:
        fields['email'] = _validate_email(data['email'])
        _ensure_email_free(fields['email'], user_id)
    if 'password' in data:
        fields['password'] = _validate_password(data['password'], 'Senha muito curta')
    if 'role' in data:
        fields['role'] = _validate_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Active deve ser booleano')
        fields['active'] = data['active']
    _check_privileged_fields(data, viewer)

    user.update(fields)
    logger.info("User updated: id=%s", user.id)
    return user.to_dict(full_email=_is_subject(viewer, user)), 200


def delete_user(user_id):
    user_service.erase_user(user_id)
    logger.info("User deleted: id=%s", user_id)
    return {'message': 'Usuário deletado com sucesso'}, 200


def get_user_tasks(user_id, args):
    tasks = user_service.get_user_tasks(user_id, parse_pagination(args))
    return [task.to_user_task_dict() for task in tasks], 200
