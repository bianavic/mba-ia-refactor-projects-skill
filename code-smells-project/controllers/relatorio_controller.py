"""Fluxo HTTP do relatório de vendas."""
from models import pedido_model


def relatorio_vendas():
    return {"dados": pedido_model.relatorio_vendas(), "sucesso": True}, 200
