"""Helpers sem estado: hash de senha e tokens assinados."""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

_PREFIXOS_HASH = ("scrypt:", "pbkdf2:")
_SALT_TOKEN = "auth-token"


def gerar_hash_senha(senha):
    return generate_password_hash(senha)


def verificar_senha(hash_armazenado, senha):
    if not hash_armazenado or not eh_hash(hash_armazenado):
        return False
    return check_password_hash(hash_armazenado, senha)


def eh_hash(valor):
    return isinstance(valor, str) and valor.startswith(_PREFIXOS_HASH)


def gerar_token(segredo, dados):
    return URLSafeTimedSerializer(segredo, salt=_SALT_TOKEN).dumps(dados)


def ler_token(segredo, token, validade_segundos):
    """Devolve os dados do token ou None se inválido/expirado."""
    try:
        return URLSafeTimedSerializer(segredo, salt=_SALT_TOKEN).loads(token, max_age=validade_segundos)
    except (BadSignature, SignatureExpired):
        return None
