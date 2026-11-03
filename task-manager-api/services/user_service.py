"""User use cases that read or write the user's tasks."""
from errors.exceptions import NotFound
from models.task import Task
from models.user import User


def _find_user(user_id):
    user = User.find(user_id)
    if user is None:
        raise NotFound('Usuário não encontrado')
    return user


def list_users_with_task_counts(pagination=None):
    """[(user, task_count)] — counts in one grouped query instead of one per user."""
    users = User.list_all(pagination)
    totals = Task.totals_by_user([user.id for user in users])
    return [(user, totals.get(user.id, (0, 0))[0]) for user in users]


def get_user_with_tasks(user_id, pagination=None):
    user = _find_user(user_id)
    return user, Task.list_by_user(user_id, pagination)


def get_user_tasks(user_id, pagination=None):
    _find_user(user_id)
    return Task.list_by_user(user_id, pagination)


def erase_user(user_id):
    """Delete the user and their tasks in one transaction (behavior of the original endpoint)."""
    user = _find_user(user_id)
    Task.stage_delete_by_user(user_id)
    user.stage_delete()
    User.commit_deletion()
