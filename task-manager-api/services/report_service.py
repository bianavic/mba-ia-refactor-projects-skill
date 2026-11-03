"""Reports and statistics over tasks, users and categories."""
from datetime import datetime, timedelta

from config import settings
from errors.exceptions import NotFound
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage


def task_stats():
    """GET /tasks/stats — the single owner of the status counts and completion rate."""
    total = Task.count_all()
    by_status = Task.count_by_status()
    return {
        'total': total,
        'pending': by_status[settings.STATUS_PENDING],
        'in_progress': by_status[settings.STATUS_IN_PROGRESS],
        'done': by_status[settings.STATUS_DONE],
        'cancelled': by_status[settings.STATUS_CANCELLED],
        'overdue': len(Task.list_overdue(datetime.utcnow())),
        'completion_rate': calculate_percentage(by_status[settings.STATUS_DONE], total),
    }


def summary():
    now = datetime.utcnow()
    since = now - timedelta(days=settings.RECENT_ACTIVITY_DAYS)
    by_status = Task.count_by_status()
    by_priority = Task.count_by_priority()
    overdue = Task.list_overdue(now)

    users = User.list_all()
    totals = Task.totals_by_user([user.id for user in users])
    productivity = []
    for user in users:
        total, completed = totals.get(user.id, (0, 0))
        productivity.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    return {
        'generated_at': str(datetime.utcnow()),
        'overview': {
            'total_tasks': Task.count_all(),
            'total_users': User.count_all(),
            'total_categories': Category.count_all(),
        },
        'tasks_by_status': {status: by_status[status] for status in settings.VALID_STATUSES},
        'tasks_by_priority': {label: by_priority[priority]
                              for priority, label in settings.PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue),
            'tasks': [{
                'id': task.id,
                'title': task.title,
                'due_date': str(task.due_date),
                'days_overdue': (now - task.due_date).days,
            } for task in overdue],
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(since),
            'tasks_completed_last_7_days': Task.count_done_updated_since(since),
        },
        'user_productivity': productivity,
    }


def user_report(user_id):
    """(user, statistics) — the caller decides how much of the user to show."""
    user = User.find(user_id)
    if user is None:
        raise NotFound('Usuário não encontrado')
    tasks = Task.list_by_user(user_id)
    counts = {status: 0 for status in settings.VALID_STATUSES}
    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1
    statistics = {
        'total_tasks': len(tasks),
        'done': counts[settings.STATUS_DONE],
        'pending': counts[settings.STATUS_PENDING],
        'in_progress': counts[settings.STATUS_IN_PROGRESS],
        'cancelled': counts[settings.STATUS_CANCELLED],
        'overdue': sum(1 for task in tasks if task.is_overdue()),
        'high_priority': sum(1 for task in tasks if task.is_high_priority()),
        'completion_rate': calculate_percentage(counts[settings.STATUS_DONE], len(tasks)),
    }
    return user, statistics
