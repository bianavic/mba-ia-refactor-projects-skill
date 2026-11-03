"""Rotas administrativas (somente admin)."""
from flask import Blueprint, g, jsonify, request

from controllers import admin_controller
from middleware.auth import requer_admin

bp = Blueprint("admin", __name__)


@bp.post("/admin/reset-db")
@requer_admin
def reset_database():
    corpo, status = admin_controller.resetar_banco(g.usuario)
    return jsonify(corpo), status


@bp.post("/admin/query")
@requer_admin
def executar_query():
    corpo, status = admin_controller.executar_query(g.usuario, request.get_json(silent=True))
    return jsonify(corpo), status
