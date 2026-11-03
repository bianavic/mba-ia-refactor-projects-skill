"""Rotas de produtos."""
from flask import Blueprint, jsonify, request

from controllers import produto_controller
from middleware.auth import requer_admin
from utils.paginacao import ler_paginacao

bp = Blueprint("produtos", __name__)


@bp.get("/produtos")
def listar_produtos():
    corpo, status = produto_controller.listar_produtos(ler_paginacao(request.args))
    return jsonify(corpo), status


@bp.get("/produtos/busca")
def buscar_produtos():
    corpo, status = produto_controller.buscar_produtos(request.args, ler_paginacao(request.args))
    return jsonify(corpo), status


@bp.get("/produtos/<int:id>")
def obter_produto(id):
    corpo, status = produto_controller.obter_produto(id)
    return jsonify(corpo), status


@bp.post("/produtos")
@requer_admin
def criar_produto():
    corpo, status = produto_controller.criar_produto(request.get_json(silent=True))
    return jsonify(corpo), status


@bp.put("/produtos/<int:id>")
@requer_admin
def atualizar_produto(id):
    corpo, status = produto_controller.atualizar_produto(id, request.get_json(silent=True))
    return jsonify(corpo), status


@bp.delete("/produtos/<int:id>")
@requer_admin
def deletar_produto(id):
    corpo, status = produto_controller.deletar_produto(id)
    return jsonify(corpo), status
