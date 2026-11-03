"""Configuração da aplicação: segredos e flags vêm do ambiente; constantes de domínio ficam aqui."""
import os
import secrets


def _bool(nome, padrao=False):
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "on")


# Implantação
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
SECRET_KEY_GERADA = "SECRET_KEY" not in os.environ
DEBUG = _bool("APP_DEBUG", False)
HOST = os.environ.get("APP_HOST", "0.0.0.0")
PORT = int(os.environ.get("APP_PORT", "5000"))
DB_PATH = os.environ.get("DB_PATH", "loja.db")
TOKEN_TTL_SEGUNDOS = int(os.environ.get("TOKEN_TTL_SECONDS", "3600"))
ADMIN_QUERY_ENABLED = _bool("ADMIN_QUERY_ENABLED", False)

# Credenciais do seed (nunca literais no código)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
SEED_CUSTOMER_PASSWORD = os.environ.get("SEED_CUSTOMER_PASSWORD")

# Domínio
VERSAO = "1.0.0"
CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
STATUS_PEDIDO = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
STATUS_PEDIDO_INICIAL = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
TIPO_USUARIO_PADRAO = "cliente"
TIPO_USUARIO_ADMIN = "admin"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

# Desconto do relatório de vendas: (faturamento acima de, taxa), da maior faixa para a menor
FAIXAS_DESCONTO = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]

# Paginação opcional
POR_PAGINA_PADRAO = 20
POR_PAGINA_MAX = 100
