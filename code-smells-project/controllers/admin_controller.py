import logging

from flask import jsonify, request

from models import admin_model

logger = logging.getLogger(__name__)


def reset_database():
    admin_model.reset_database()
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    dados = request.get_json()
    tabela = dados.get("tabela", "") if dados else ""
    if not tabela:
        return jsonify({"erro": "Tabela não informada"}), 400

    try:
        resultado = admin_model.executar_query(tabela)
        return jsonify({"dados": resultado, "sucesso": True}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
