import logging
import re

from flask import abort, current_app
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func

from database import db
from models.user import User
from models.task import Task
from utils.helpers import VALID_ROLES, MIN_PASSWORD_LENGTH

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def _login_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='login-token')


def list_users(page, per_page):
    users = User.query.paginate(page=page, per_page=per_page, error_out=False).items

    user_ids = [u.id for u in users]
    task_counts = dict(
        db.session.query(Task.user_id, func.count(Task.id))
        .filter(Task.user_id.in_(user_ids))
        .group_by(Task.user_id).all()
    )

    result = []
    for u in users:
        user_data = {
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'role': u.role,
            'active': u.active,
            'created_at': str(u.created_at),
            'task_count': task_counts.get(u.id, 0)
        }
        result.append(user_data)
    return result


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404, description='Usuário não encontrado')

    data = user.to_dict()

    tasks = Task.query.filter_by(user_id=user_id).all()
    data['tasks'] = [t.to_dict() for t in tasks]

    return data


def create_user(data):
    if not data:
        abort(400, description='Dados inválidos')

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        abort(400, description='Nome é obrigatório')
    if not email:
        abort(400, description='Email é obrigatório')
    if not password:
        abort(400, description='Senha é obrigatória')

    if not EMAIL_REGEX.match(email):
        abort(400, description='Email inválido')

    if len(password) < MIN_PASSWORD_LENGTH:
        abort(400, description='Senha deve ter no mínimo 4 caracteres')

    existing = User.query.filter_by(email=email).first()
    if existing:
        abort(409, description='Email já cadastrado')

    if role not in VALID_ROLES:
        abort(400, description='Role inválido')

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    try:
        db.session.add(user)
        db.session.commit()
        logger.info(f"Usuário criado: {user.id} - {user.name}")
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao criar usuário", exc_info=e)
        abort(500, description='Erro ao criar usuário')

    return user.to_dict()


def update_user(user_id, data):
    user = db.session.get(User, user_id)
    if not user:
        abort(404, description='Usuário não encontrado')

    if not data:
        abort(400, description='Dados inválidos')

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        if not EMAIL_REGEX.match(data['email']):
            abort(400, description='Email inválido')

        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            abort(409, description='Email já cadastrado')
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            abort(400, description='Senha muito curta')
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            abort(400, description='Role inválido')
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao atualizar usuário", exc_info=e)
        abort(500, description='Erro ao atualizar')

    return user.to_dict()


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404, description='Usuário não encontrado')

    try:
        Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.delete(user)
        db.session.commit()
        logger.info(f"Usuário deletado: {user_id}")
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao deletar usuário", exc_info=e)
        abort(500, description='Erro ao deletar')


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404, description='Usuário não encontrado')

    tasks = Task.query.filter_by(user_id=user_id).all()
    result = []
    for t in tasks:
        task_data = t.to_dict()
        for field in ('user_id', 'category_id', 'updated_at', 'tags'):
            del task_data[field]
        result.append(task_data)

    return result


def login(data):
    if not data:
        abort(400, description='Dados inválidos')

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        abort(400, description='Email e senha são obrigatórios')

    user = User.query.filter_by(email=email).first()
    if not user:
        abort(401, description='Credenciais inválidas')

    if not user.check_password(password):
        abort(401, description='Credenciais inválidas')

    if not user.active:
        abort(403, description='Usuário inativo')

    token = _login_serializer().dumps({'user_id': user.id})

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token
    }
