"""Optional pagination: without page/per_page the full list is returned (unchanged contract)."""
from config import settings
from errors.exceptions import ValidationError


def _positive_int(raw, name):
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValidationError(f'Parâmetro {name} inválido')
    if value < 1:
        raise ValidationError(f'Parâmetro {name} inválido')
    return value


def parse_pagination(args):
    """(page, per_page) when either parameter is present, else None. Invalid values → 400."""
    if 'page' not in args and 'per_page' not in args:
        return None
    page = _positive_int(args.get('page', 1), 'page')
    per_page = _positive_int(args.get('per_page', settings.DEFAULT_PER_PAGE), 'per_page')
    if per_page > settings.MAX_PER_PAGE:
        raise ValidationError(f'Parâmetro per_page deve ser no máximo {settings.MAX_PER_PAGE}')
    return page, per_page
