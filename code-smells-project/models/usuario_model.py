"""Acesso a dados de usuários. A senha nunca sai deste módulo."""
from config import settings
from database.connection import confirmar, get_db
from utils.paginacao import clausula_sql
from utils.seguranca import eh_hash, gerar_hash_senha, verificar_senha


def _serializar(row):
    """Campos públicos — nunca a senha."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def listar(paginacao=None):
    limite, params = clausula_sql(paginacao)
    rows = get_db().execute("SELECT * FROM usuarios ORDER BY id" + limite, params).fetchall()
    return [_serializar(r) for r in rows]


def obter_por_id(id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (id,)).fetchone()
    return _serializar(row) if row else None


def existe(id):
    return get_db().execute("SELECT 1 FROM usuarios WHERE id = ?", (id,)).fetchone() is not None


def verificar_credenciais(email, senha):
    rows = get_db().execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()
    for row in rows:
        if verificar_senha(row["senha"], senha):
            return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    return None


def criar(nome, email, senha, tipo=settings.TIPO_USUARIO_PADRAO):
    cursor = get_db().execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, gerar_hash_senha(senha), tipo),
    )
    confirmar()
    return cursor.lastrowid


def deletar(id):
    get_db().execute("DELETE FROM usuarios WHERE id = ?", (id,))
    confirmar()


def migrar_senhas_em_texto_puro():
    """Converte em hash toda senha ainda armazenada em texto puro. Devolve quantas migrou."""
    db = get_db()
    rows = db.execute("SELECT id, senha FROM usuarios").fetchall()
    migradas = 0
    for row in rows:
        if row["senha"] is not None and not eh_hash(row["senha"]):
            db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (gerar_hash_senha(row["senha"]), row["id"]))
            migradas += 1
    db.commit()
    return migradas


def contar():
    return get_db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]


def apagar_todos():
    get_db().execute("DELETE FROM usuarios")
    confirmar()
