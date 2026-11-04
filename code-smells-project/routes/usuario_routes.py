"""Rotas de usuários e login."""
from flask import Blueprint, g, jsonify, request

from controllers import usuario_controller
from middleware.auth import dono_ou_admin, dono_pelo_id_do_usuario, requer_admin
from utils.paginacao import ler_paginacao

bp = Blueprint("usuarios", __name__)


@bp.get("/usuarios")
@requer_admin
def listar_usuarios():
    corpo, status = usuario_controller.listar_usuarios(g.usuario, ler_paginacao(request.args))
    return jsonify(corpo), status


@bp.get("/usuarios/<int:id>")
@dono_ou_admin(dono_pelo_id_do_usuario)
def obter_usuario(id):
    corpo, status = usuario_controller.obter_usuario(id, g.usuario)
    return jsonify(corpo), status


@bp.post("/usuarios")
def criar_usuario():
    corpo, status = usuario_controller.criar_usuario(request.get_json(silent=True))
    return jsonify(corpo), status


@bp.post("/login")
def login():
    corpo, status = usuario_controller.login(request.get_json(silent=True))
    return jsonify(corpo), status


@bp.delete("/usuarios/<int:id>")
@dono_ou_admin(dono_pelo_id_do_usuario)
def excluir_usuario(id):
    corpo, status = usuario_controller.excluir_usuario(id)
    return jsonify(corpo), status


@bp.get("/usuarios/<int:id>/export")
@dono_ou_admin(dono_pelo_id_do_usuario)
def exportar_usuario(id):
    corpo, status = usuario_controller.exportar_usuario(id, g.usuario)
    return jsonify(corpo), status
