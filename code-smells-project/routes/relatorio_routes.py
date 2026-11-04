"""Rotas de relatórios."""
from flask import Blueprint, jsonify

from controllers import relatorio_controller
from middleware.auth import requer_admin

bp = Blueprint("relatorios", __name__)


@bp.get("/relatorios/vendas")
@requer_admin
def relatorio_vendas():
    corpo, status = relatorio_controller.relatorio_vendas()
    return jsonify(corpo), status
