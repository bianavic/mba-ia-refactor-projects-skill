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

NOME_PRODUTO_MIN_LEN = 2
NOME_PRODUTO_MAX_LEN = 200

# Faixas de desconto aplicadas ao faturamento bruto no relatório de vendas,
# da maior para a menor: (faturamento_minimo, taxa_de_desconto).
FAIXAS_DESCONTO_FATURAMENTO = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]
