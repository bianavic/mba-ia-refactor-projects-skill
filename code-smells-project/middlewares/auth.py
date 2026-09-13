from functools import wraps

from flask import jsonify, request

from config.settings import ADMIN_TOKEN


def requer_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not ADMIN_TOKEN:
            return jsonify({"erro": "Endpoints administrativos desabilitados"}), 403
        if request.headers.get("X-Admin-Token") != ADMIN_TOKEN:
            return jsonify({"erro": "Não autorizado"}), 401
        return fn(*args, **kwargs)

    return wrapper
