import logging

from flask import jsonify, request

from models import product_model
from utils.pagination import parse_pagination

logger = logging.getLogger(__name__)


def listar():
    try:
        page, per_page = parse_pagination()
        produtos = product_model.get_todos(page, per_page)
        logger.info("Listando %d produtos (page=%d)", len(produtos), page)
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception as e:
        logger.exception("Erro ao listar produtos")
        return jsonify({"erro": str(e)}), 500


def buscar_por_id(produto_id):
    try:
        produto = product_model.get_por_id(produto_id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


def criar():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
            if campo not in dados:
                return jsonify({"erro": f"{rotulo} é obrigatório"}), 400

        produto_id = product_model.criar(
            nome=dados["nome"],
            descricao=dados.get("descricao", ""),
            preco=dados["preco"],
            estoque=dados["estoque"],
            categoria=dados.get("categoria", "geral"),
        )
        logger.info("Produto criado com ID: %s", produto_id)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        logger.exception("Erro ao criar produto")
        return jsonify({"erro": str(e)}), 500


def atualizar(produto_id):
    try:
        if not product_model.get_por_id(produto_id):
            return jsonify({"erro": "Produto não encontrado"}), 404

        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
            if campo not in dados:
                return jsonify({"erro": f"{rotulo} é obrigatório"}), 400

        product_model.atualizar(
            produto_id,
            nome=dados["nome"],
            descricao=dados.get("descricao", ""),
            preco=dados["preco"],
            estoque=dados["estoque"],
            categoria=dados.get("categoria", "geral"),
        )
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


def deletar(produto_id):
    try:
        if not product_model.get_por_id(produto_id):
            return jsonify({"erro": "Produto não encontrado"}), 404
        product_model.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


def buscar():
    try:
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)
        page, per_page = parse_pagination()

        if preco_min:
            preco_min = float(preco_min)
        if preco_max:
            preco_max = float(preco_max)

        resultados = product_model.buscar(termo, categoria, preco_min, preco_max, page, per_page)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
