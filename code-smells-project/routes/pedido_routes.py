"""Rotas de pedidos."""
from flask import Blueprint, jsonify, request

from controllers import pedido_controller
from middleware.auth import (dono_ou_admin, dono_pelo_usuario_id_da_rota,
                             dono_pelo_usuario_id_do_corpo, requer_admin)
from utils.paginacao import ler_paginacao

bp = Blueprint("pedidos", __name__)


@bp.post("/pedidos")
@dono_ou_admin(dono_pelo_usuario_id_do_corpo)
def criar_pedido():
    corpo, status = pedido_controller.criar_pedido(request.get_json(silent=True))
    return jsonify(corpo), status


@bp.get("/pedidos")
@requer_admin
def listar_todos_pedidos():
    corpo, status = pedido_controller.listar_todos_pedidos(ler_paginacao(request.args))
    return jsonify(corpo), status


@bp.get("/pedidos/usuario/<int:usuario_id>")
@dono_ou_admin(dono_pelo_usuario_id_da_rota)
def listar_pedidos_usuario(usuario_id):
    corpo, status = pedido_controller.listar_pedidos_usuario(usuario_id, ler_paginacao(request.args))
    return jsonify(corpo), status


@bp.put("/pedidos/<int:pedido_id>/status")
@requer_admin
def atualizar_status_pedido(pedido_id):
    corpo, status = pedido_controller.atualizar_status_pedido(pedido_id, request.get_json(silent=True))
    return jsonify(corpo), status
