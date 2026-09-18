import logging

from flask import abort
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import DEFAULT_PRIORITY, utc_now

logger = logging.getLogger(__name__)


def _validate_title(title, required=True):
    if not title:
        if required:
            abort(400, description='Título é obrigatório')
        return
    error = Task.title_error(title)
    if error:
        abort(400, description=error)


def _validate_status(status):
    if not Task.validate_status(status):
        abort(400, description='Status inválido')


def _validate_priority(priority):
    if not Task.validate_priority(priority):
        abort(400, description='Prioridade deve ser entre 1 e 5')


def _resolve_user(user_id):
    if user_id and not db.session.get(User, user_id):
        abort(404, description='Usuário não encontrado')


def _resolve_category(category_id):
    if category_id and not db.session.get(Category, category_id):
        abort(404, description='Categoria não encontrada')


def _apply_due_date(task, due_date, invalid_format_message):
    if due_date:
        try:
            task.due_date = Task.parse_due_date(due_date)
        except ValueError:
            abort(400, description=invalid_format_message)
    else:
        task.due_date = None


def list_tasks(page, per_page):
    tasks = Task.query.options(
        joinedload(Task.user), joinedload(Task.category)
    ).paginate(page=page, per_page=per_page, error_out=False).items

    result = []
    for t in tasks:
        task_data = t.to_dict()
        task_data['user_name'] = t.user.name if t.user else None
        task_data['category_name'] = t.category.name if t.category else None
        result.append(task_data)
    return result


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        abort(404, description='Task não encontrada')
    return task.to_dict()


def create_task(data):
    if not data:
        abort(400, description='Dados inválidos')

    title = data.get('title')
    _validate_title(title, required=True)

    status = data.get('status', 'pending')
    _validate_status(status)

    priority = data.get('priority', DEFAULT_PRIORITY)
    _validate_priority(priority)

    user_id = data.get('user_id')
    _resolve_user(user_id)

    category_id = data.get('category_id')
    _resolve_category(category_id)

    task = Task()
    task.title = title
    task.description = data.get('description', '')
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    _apply_due_date(task, data.get('due_date'), 'Formato de data inválido. Use YYYY-MM-DD')

    tags = data.get('tags')
    if tags:
        task.tags = Task.normalize_tags(tags)

    try:
        db.session.add(task)
        db.session.commit()
        logger.info(f"Task criada: {task.id} - {task.title}")
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao criar task", exc_info=e)
        abort(500, description='Erro ao criar task')

    return task.to_dict()


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        abort(404, description='Task não encontrada')

    if not data:
        abort(400, description='Dados inválidos')

    if 'title' in data:
        _validate_title(data['title'], required=False)
        task.title = data['title']

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        _validate_status(data['status'])
        task.status = data['status']

    if 'priority' in data:
        _validate_priority(data['priority'])
        task.priority = data['priority']

    if 'user_id' in data:
        _resolve_user(data['user_id'])
        task.user_id = data['user_id']

    if 'category_id' in data:
        _resolve_category(data['category_id'])
        task.category_id = data['category_id']

    if 'due_date' in data:
        _apply_due_date(task, data['due_date'], 'Formato de data inválido')

    if 'tags' in data:
        task.tags = Task.normalize_tags(data['tags']) if data['tags'] else data['tags']

    task.updated_at = utc_now()

    try:
        db.session.commit()
        logger.info(f"Task atualizada: {task.id}")
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao atualizar task", exc_info=e)
        abort(500, description='Erro ao atualizar')

    return task.to_dict()


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        abort(404, description='Task não encontrada')

    try:
        db.session.delete(task)
        db.session.commit()
        logger.info(f"Task deletada: {task_id}")
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao deletar task", exc_info=e)
        abort(500, description='Erro ao deletar')


def search_tasks(query, status, priority, user_id, page, per_page):
    tasks = Task.search(
        query=query,
        status=status,
        priority=priority,
        user_id=user_id,
    ).paginate(page=page, per_page=per_page, error_out=False).items

    return [t.to_dict() for t in tasks]


def task_stats():
    return Task.get_statistics()
