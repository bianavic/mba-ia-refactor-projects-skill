"""Autenticação (Bearer token assinado) e autorização por papel/dono."""
from functools import wraps

from flask import current_app, g, request

from config import settings
from errors.exceptions import Forbidden, Unauthorized
from utils.seguranca import ler_token


def _usuario_do_token():
    cabecalho = request.headers.get("Authorization", "")
    if not cabecalho.startswith("Bearer "):
        raise Unauthorized("Autenticação necessária")
    dados = ler_token(current_app.config["SECRET_KEY"], cabecalho[len("Bearer "):].strip(),
                      settings.TOKEN_TTL_SEGUNDOS)
    if not dados or "id" not in dados or "tipo" not in dados:
        raise Unauthorized("Token inválido ou expirado")
    return dados


def eh_admin(usuario):
    return usuario is not None and usuario.get("tipo") == settings.TIPO_USUARIO_ADMIN


def requer_admin(fn):
    @wraps(fn)
    def envoltorio(*args, **kwargs):
        g.usuario = _usuario_do_token()
        if not eh_admin(g.usuario):
            raise Forbidden("Acesso negado")
        return fn(*args, **kwargs)
    return envoltorio


def dono_ou_admin(resolver_dono):
    """resolver_dono(kwargs) → id do titular do recurso, ou None se ainda não informado
    (a validação do controller responde 400 nesse caso)."""
    def decorador(fn):
        @wraps(fn)
        def envoltorio(*args, **kwargs):
            g.usuario = _usuario_do_token()
            if not eh_admin(g.usuario):
                dono = resolver_dono(kwargs)
                if dono is not None and dono != g.usuario["id"]:
                    raise Forbidden("Acesso negado")
            return fn(*args, **kwargs)
        return envoltorio
    return decorador


# Resolvedores de dono (recurso → identidade do titular persistida)
def dono_pelo_id_do_usuario(kwargs):
    """/usuarios/<id>: o titular do usuário é ele mesmo."""
    return kwargs.get("id")


def dono_pelo_usuario_id_da_rota(kwargs):
    """/pedidos/usuario/<usuario_id>: os pedidos pertencem a usuario_id."""
    return kwargs.get("usuario_id")


def dono_pelo_usuario_id_do_corpo(_kwargs):
    """POST /pedidos: o pedido será do usuario_id enviado no corpo."""
    dados = request.get_json(silent=True)
    if isinstance(dados, dict) and "usuario_id" in dados:
        return dados["usuario_id"]
    return None
