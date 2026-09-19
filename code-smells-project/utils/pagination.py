from flask import request

from config.settings import DEFAULT_PAGE, DEFAULT_PER_PAGE


def parse_pagination():
    page = int(request.args.get("page", DEFAULT_PAGE))
    per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
    return page, per_page
