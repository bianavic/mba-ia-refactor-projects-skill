import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
DB_PATH = os.environ.get("DB_PATH", "loja.db")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))

# Unset by default -> admin endpoints are disabled until an operator opts in.
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

PRODUTO_CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
PEDIDO_STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
