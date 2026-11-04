"""Paginação opcional: sem page/per_page devolve None (lista completa, como antes)."""
from config import settings
from errors.exceptions import ValidationError


def ler_paginacao(args):
    if "page" not in args and "per_page" not in args:
        return None
    pagina = _inteiro(args.get("page", "1"), "page")
    por_pagina = _inteiro(args.get("per_page", str(settings.POR_PAGINA_PADRAO)), "per_page")
    if pagina < 1:
        raise ValidationError("page deve ser um inteiro >= 1")
    if por_pagina < 1 or por_pagina > settings.POR_PAGINA_MAX:
        raise ValidationError("per_page deve ser um inteiro entre 1 e " + str(settings.POR_PAGINA_MAX))
    return {"limite": por_pagina, "deslocamento": (pagina - 1) * por_pagina}


def _inteiro(valor, nome):
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValidationError(nome + " deve ser um inteiro")


def clausula_sql(paginacao):
    """Fragmento LIMIT/OFFSET com parâmetros vinculados."""
    if paginacao is None:
        return "", []
    return " LIMIT ? OFFSET ?", [paginacao["limite"], paginacao["deslocamento"]]
