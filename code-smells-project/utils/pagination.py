from flask import request

from config.settings import DEFAULT_PAGE, DEFAULT_PER_PAGE


def parse_pagination():
    try:
        page = int(request.args.get("page", DEFAULT_PAGE))
        per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
    except (TypeError, ValueError):
        raise ValueError("page e per_page devem ser números inteiros")
    return page, per_page
