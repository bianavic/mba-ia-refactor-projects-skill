"""Rotas de boas-vindas e health check."""
from flask import Blueprint, jsonify

from controllers import sistema_controller

bp = Blueprint("sistema", __name__)


@bp.get("/")
def index():
    corpo, status = sistema_controller.index()
    return jsonify(corpo), status


@bp.get("/health")
def health_check():
    corpo, status = sistema_controller.health_check()
    return jsonify(corpo), status
