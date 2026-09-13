import logging

from flask import jsonify, request

from config.settings import DEFAULT_PAGE, DEFAULT_PER_PAGE, PEDIDO_STATUS_VALIDOS
from models import order_model

logger = logging.getLogger(__name__)


def criar():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

        resultado = order_model.criar(usuario_id, itens)
        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        logger.info("Notificação (email) enviada: pedido %s criado para usuario %s", resultado["pedido_id"], usuario_id)
        logger.info("Notificação (sms) enviada: pedido recebido")
        logger.info("Notificação (push) enviada: novo pedido no sistema")

        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201
    except Exception as e:
        logger.exception("Erro crítico ao criar pedido")
        return jsonify({"erro": str(e)}), 500


def listar_por_usuario(usuario_id):
    try:
        pedidos = order_model.get_por_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


def listar_todos():
    try:
        page = int(request.args.get("page", DEFAULT_PAGE))
        per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
        pedidos = order_model.get_todos(page, per_page)
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


def atualizar_status(pedido_id):
    try:
        dados = request.get_json()
        novo_status = dados.get("status", "")

        if novo_status not in PEDIDO_STATUS_VALIDOS:
            return jsonify({"erro": "Status inválido"}), 400

        order_model.atualizar_status(pedido_id, novo_status)

        if novo_status == "aprovado":
            logger.info("Pedido %s aprovado. Preparar envio.", pedido_id)
        if novo_status == "cancelado":
            logger.info("Pedido %s cancelado. Devolver estoque.", pedido_id)

        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


def relatorio_vendas():
    try:
        relatorio = order_model.relatorio_vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
