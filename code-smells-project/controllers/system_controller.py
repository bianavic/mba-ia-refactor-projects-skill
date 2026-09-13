from flask import jsonify

from models import order_model, product_model, user_model


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health_check():
    try:
        counts = {
            "produtos": product_model.count(),
            "usuarios": user_model.count(),
            "pedidos": order_model.count(),
        }
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": counts,
            "versao": "1.0.0",
        }), 200
    except Exception as e:
        return jsonify({"status": "erro", "detalhes": str(e)}), 500
