"""Task use cases that touch other entities: assignment to a user and to a category."""
from errors.exceptions import NotFound
from models.category import Category
from models.task import Task
from models.user import User


def _check_references(fields):
    if fields.get('user_id') is not None and User.find(fields['user_id']) is None:
        raise NotFound('Usuário não encontrado')
    if fields.get('category_id') is not None and Category.find(fields['category_id']) is None:
        raise NotFound('Categoria não encontrada')


def ensure_task_exists(task_id):
    task = Task.find(task_id)
    if task is None:
        raise NotFound('Task não encontrada')
    return task


def create_task(fields):
    _check_references(fields)
    return Task.create(fields)


def update_task(task_id, fields):
    task = ensure_task_exists(task_id)
    _check_references(fields)
    return task.update(fields)
