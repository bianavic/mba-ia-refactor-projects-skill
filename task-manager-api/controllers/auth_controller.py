"""Login: verifies the credential and issues a signed, expiring token."""
import logging

from errors.exceptions import Forbidden, Unauthorized, ValidationError
from models.user import User
from utils.security import create_token

logger = logging.getLogger(__name__)


def login(data, secret_key):
    if not isinstance(data, dict) or not data:
        raise ValidationError('Dados inválidos')
    email = data.get('email')
    password = data.get('password')
    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Email e senha são obrigatórios')

    user = User.find_by_email(email)
    if user is None or not user.check_password(password):
        raise Unauthorized('Credenciais inválidas')
    if not user.active:
        raise Forbidden('Usuário inativo')
    if user.needs_rehash():
        user.upgrade_password_hash(password)
        logger.info("Legacy password hash upgraded: user id=%s", user.id)

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(full_email=True),
        'token': create_token(secret_key, {'id': user.id}),
    }, 200
