"""Task request flow: validation, one Service/Model call, status and response shape."""
import logging
from datetime import datetime

from config import settings
from errors.exceptions import NotFound, ValidationError
from models.task import Task
from services import report_service, task_service
from utils.pagination import parse_pagination

logger = logging.getLogger(__name__)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _require_body(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError('Dados inválidos')


def _validate_title(title, required):
    if title is None or title == '':
        if required:
            raise ValidationError('Título é obrigatório')
        raise ValidationError('Título muito curto')
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < settings.MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > settings.MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _validate_priority(priority):
    if not _is_int(priority):
        raise ValidationError('Prioridade deve ser um número inteiro')
    if priority < settings.MIN_PRIORITY or priority > settings.MAX_PRIORITY:
        raise ValidationError(f'Prioridade deve ser entre {settings.MIN_PRIORITY} e {settings.MAX_PRIORITY}')
    return priority


def _validate_reference(value, field):
    if value is not None and not _is_int(value):
        raise ValidationError(f'{field} inválido')
    return value


def _parse_due_date(value, message):
    if not isinstance(value, str):
        raise ValidationError(message)
    try:
        return datetime.strptime(value, settings.DATE_FORMAT)
    except ValueError:
        raise ValidationError(message)


def _validate_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return settings.TAG_SEPARATOR.join(tags)
    if tags is None or isinstance(tags, str):
        return tags
    raise ValidationError('Tags inválidas')


def validate_task(data, partial):
    """One validator for create (partial=False) and update (partial=True); returns the fields to store."""
    _require_body(data)
    fields = {}
    if not partial or 'title' in data:
        fields['title'] = _validate_title(data.get('title'), required=not partial)
    if not partial or 'description' in data:
        description = data.get('description', '') if not partial else data['description']
        if description is not None and not isinstance(description, str):
            raise ValidationError('Descrição inválida')
        fields['description'] = description
    if not partial or 'status' in data:
        status = data.get('status', settings.DEFAULT_STATUS)
        if not isinstance(status, str) or status not in settings.VALID_STATUSES:
            raise ValidationError('Status inválido')
        fields['status'] = status
    if not partial or 'priority' in data:
        fields['priority'] = _validate_priority(data.get('priority', settings.DEFAULT_PRIORITY))
    for field in ('user_id', 'category_id'):
        if not partial or field in data:
            fields[field] = _validate_reference(data.get(field), field)
    if 'due_date' in data:
        if data['due_date']:
            message = 'Formato de data inválido' if partial else 'Formato de data inválido. Use YYYY-MM-DD'
            fields['due_date'] = _parse_due_date(data['due_date'], message)
        elif partial:
            fields['due_date'] = None
    if 'tags' in data:
        tags = _validate_tags(data['tags'])
        if partial or tags:
            fields['tags'] = tags
    return fields


def _parse_int_param(raw, name):
    if raw in (None, ''):
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValidationError(f'Parâmetro {name} inválido')


# ---------- handlers ----------

def list_tasks(args):
    return [task.to_list_dict() for task in Task.list_all(parse_pagination(args))], 200


def get_task(task_id):
    task = Task.find(task_id)
    if task is None:
        raise NotFound('Task não encontrada')
    return task.to_detail_dict(), 200


def create_task(data):
    task = task_service.create_task(validate_task(data, partial=False))
    logger.info("Task created: id=%s", task.id)
    return task.to_dict(), 201


def update_task(task_id, data):
    task_service.ensure_task_exists(task_id)
    task = task_service.update_task(task_id, validate_task(data, partial=True))
    logger.info("Task updated: id=%s", task.id)
    return task.to_dict(), 200


def delete_task(task_id):
    task = Task.find(task_id)
    if task is None:
        raise NotFound('Task não encontrada')
    task.delete()
    logger.info("Task deleted: id=%s", task_id)
    return {'message': 'Task deletada com sucesso'}, 200


def search_tasks(args):
    tasks = Task.search(
        text=args.get('q', ''),
        status=args.get('status', ''),
        priority=_parse_int_param(args.get('priority'), 'priority'),
        user_id=_parse_int_param(args.get('user_id'), 'user_id'),
        pagination=parse_pagination(args),
    )
    return [task.to_dict() for task in tasks], 200


def task_stats():
    return report_service.task_stats(), 200
