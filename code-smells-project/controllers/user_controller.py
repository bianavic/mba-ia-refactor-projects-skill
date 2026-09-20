import logging

from flask import jsonify, request

from models import user_model
from utils.pagination import parse_pagination

logger = logging.getLogger(__name__)


def listar():
    try:
        page, per_page = parse_pagination()
        usuarios = user_model.get_todos(page, per_page)
        return jsonify({"dados": usuarios, "sucesso": True}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


def buscar_por_id(usuario_id):
    try:
        usuario = user_model.get_por_id(usuario_id)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True}), 200
        return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


def criar():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not nome or not email or not senha:
            return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

        usuario_id = user_model.criar(nome, email, senha)
        logger.info("Usuário criado: %s", email)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


def login():
    try:
        dados = request.get_json()
        email = dados.get("email", "") if dados else ""
        senha = dados.get("senha", "") if dados else ""

        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400

        usuario = user_model.autenticar(email, senha)
        if usuario:
            logger.info("Login bem-sucedido: %s", email)
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

        logger.info("Login falhou: %s", email)
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
