"""Conexão por requisição, transações, schema e seed do SQLite."""
import logging
import sqlite3
from contextlib import contextmanager

from flask import g

from config import settings
from utils.seguranca import gerar_hash_senha

logger = logging.getLogger(__name__)


def get_db():
    """Uma conexão por contexto de aplicação, fechada no teardown."""
    if "db" not in g:
        g.db = sqlite3.connect(settings.DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def fechar_db(_erro=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def confirmar():
    """Commit, exceto dentro de transacao() — aí o commit é do bloco."""
    if not g.get("em_transacao"):
        get_db().commit()


@contextmanager
def transacao():
    db = get_db()
    if g.get("em_transacao"):
        yield db
        return
    db.execute("BEGIN IMMEDIATE")
    g.em_transacao = True
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        g.em_transacao = False


def executar_sql_bruto(sql):
    """Executa SQL arbitrário (somente /admin/query, quando habilitado)."""
    db = get_db()
    cursor = db.execute(sql)
    if sql.strip().upper().startswith("SELECT"):
        return [dict(row) for row in cursor.fetchall()]
    db.commit()
    return None


_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT,
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
]

_PRODUTOS_SEED = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]


def _usuarios_seed():
    """Contas do seed; uma conta sem senha no ambiente não é criada."""
    usuarios = []
    if settings.ADMIN_PASSWORD:
        usuarios.append(("Admin", "admin@loja.com", settings.ADMIN_PASSWORD, settings.TIPO_USUARIO_ADMIN))
    else:
        logger.warning("ADMIN_PASSWORD não definido: conta admin não semeada")
    if settings.SEED_CUSTOMER_PASSWORD:
        usuarios.append(("João Silva", "joao@email.com", settings.SEED_CUSTOMER_PASSWORD, settings.TIPO_USUARIO_PADRAO))
        usuarios.append(("Maria Santos", "maria@email.com", settings.SEED_CUSTOMER_PASSWORD, settings.TIPO_USUARIO_PADRAO))
    else:
        logger.warning("SEED_CUSTOMER_PASSWORD não definido: clientes de exemplo não semeados")
    return [(nome, email, gerar_hash_senha(senha), tipo) for nome, email, senha, tipo in usuarios]


def inicializar_db():
    """Cria o schema e semeia dados de exemplo; chamado no boot dentro do app context."""
    db = get_db()
    for ddl in _SCHEMA:
        db.execute(ddl)
    db.commit()

    if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            _PRODUTOS_SEED,
        )
        db.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            _usuarios_seed(),
        )
        db.commit()
