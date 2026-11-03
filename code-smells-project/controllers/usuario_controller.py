"""Fluxo HTTP de usuários, login e direitos do titular."""
import logging

from flask import current_app

from errors.exceptions import NotFound, Unauthorized, ValidationError
from models import usuario_model
from services import usuario_service
from utils.mascaramento import mascarar_email
from utils.seguranca import gerar_token

logger = logging.getLogger(__name__)


def _visao(usuario, solicitante):
    """Email completo só para o próprio titular; mascarado para qualquer outro (inclusive admin)."""
    visao = dict(usuario)
    if solicitante is None or solicitante["id"] != usuario["id"]:
        visao["email"] = mascarar_email(usuario["email"])
    return visao


def listar_usuarios(solicitante, paginacao):
    usuarios = usuario_model.listar(paginacao)
    return {"dados": [_visao(u, solicitante) for u in usuarios], "sucesso": True}, 200


def obter_usuario(id, solicitante):
    usuario = usuario_model.obter_por_id(id)
    if not usuario:
        raise NotFound("Usuário não encontrado")
    return {"dados": _visao(usuario, solicitante), "sucesso": True}, 200


def _texto(dados, campo):
    valor = dados.get(campo, "")
    return valor if isinstance(valor, str) else None


def criar_usuario(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    nome, email, senha = _texto(dados, "nome"), _texto(dados, "email"), _texto(dados, "senha")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    # O tipo nunca vem do corpo: cadastro público sempre cria o tipo padrão.
    id = usuario_model.criar(nome, email, senha)
    logger.info("Usuário criado: id=%s", id)
    return {"dados": {"id": id}, "sucesso": True}, 201


def login(dados):
    if not isinstance(dados, dict):
        raise ValidationError("Email e senha são obrigatórios")
    email, senha = _texto(dados, "email"), _texto(dados, "senha")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.verificar_credenciais(email, senha)
    if not usuario:
        logger.info("Login falhou: %s", mascarar_email(email))
        raise Unauthorized("Email ou senha inválidos", incluir_sucesso=True)

    logger.info("Login bem-sucedido: id=%s", usuario["id"])
    token = gerar_token(current_app.config["SECRET_KEY"], {"id": usuario["id"], "tipo": usuario["tipo"]})
    return {"dados": usuario, "token": token, "sucesso": True, "mensagem": "Login OK"}, 200


def excluir_usuario(id):
    usuario_service.excluir_usuario(id)
    logger.info("Usuário removido: id=%s", id)
    return {"sucesso": True, "mensagem": "Usuário removido"}, 200


def exportar_usuario(id, solicitante):
    dados = usuario_service.exportar_usuario(id)
    dados["usuario"] = _visao(dados["usuario"], solicitante)
    return {"dados": dados, "sucesso": True}, 200
