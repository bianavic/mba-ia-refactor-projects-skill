"""Category request flow."""
from config import settings
from errors.exceptions import NotFound, ValidationError
from models.category import Category
from services import category_service
from utils.helpers import is_valid_color
from utils.pagination import parse_pagination


def _validate_category(data, partial):
    if not isinstance(data, dict) or (not partial and not data):
        raise ValidationError('Dados inválidos')
    fields = {}
    if not partial or 'name' in data:
        name = data.get('name')
        if not isinstance(name, str) or not name.strip():
            raise ValidationError('Nome é obrigatório')
        fields['name'] = name
    if not partial or 'description' in data:
        description = data.get('description', '') if not partial else data['description']
        if description is not None and not isinstance(description, str):
            raise ValidationError('Descrição inválida')
        fields['description'] = description
    if not partial or 'color' in data:
        color = data.get('color', settings.DEFAULT_COLOR) if not partial else data['color']
        if not is_valid_color(color):
            raise ValidationError('Cor inválida. Use #RRGGBB')
        fields['color'] = color
    return fields


def list_categories(args):
    rows = category_service.list_categories_with_task_counts(parse_pagination(args))
    result = []
    for category, task_count in rows:
        data = category.to_dict()
        data['task_count'] = task_count
        result.append(data)
    return result, 200


def create_category(data):
    category = Category.create(_validate_category(data, partial=False))
    return category.to_dict(), 201


def _find(category_id):
    category = Category.find(category_id)
    if category is None:
        raise NotFound('Categoria não encontrada')
    return category


def update_category(category_id, data):
    category = _find(category_id)
    return category.update(_validate_category(data, partial=True)).to_dict(), 200


def delete_category(category_id):
    _find(category_id).delete()
    return {'message': 'Categoria deletada'}, 200
