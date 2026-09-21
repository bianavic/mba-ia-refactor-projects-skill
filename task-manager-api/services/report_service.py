import logging

from flask import abort
from sqlalchemy import func

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import (
    utc_now,
    calculate_percentage,
    DEFAULT_COLOR,
    STATUS_PENDING,
    STATUS_IN_PROGRESS,
    STATUS_DONE,
    STATUS_CANCELLED,
    OVERDUE_LIST_LIMIT,
)
from datetime import timedelta

logger = logging.getLogger(__name__)


def build_summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    status_counts = Task.status_counts()

    p1 = Task.query.filter_by(priority=1).count()
    p2 = Task.query.filter_by(priority=2).count()
    p3 = Task.query.filter_by(priority=3).count()
    p4 = Task.query.filter_by(priority=4).count()
    p5 = Task.query.filter_by(priority=5).count()

    now = utc_now()
    overdue_count = Task.overdue_count()
    overdue_tasks = (
        Task.overdue_query()
        .order_by(Task.due_date.asc())
        .limit(OVERDUE_LIST_LIMIT)
        .all()
    )
    overdue_list = [
        {
            'id': t.id,
            'title': t.title,
            'due_date': str(t.due_date),
            'days_overdue': (now - t.due_date).days
        }
        for t in overdue_tasks
    ]

    seven_days_ago = now - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == STATUS_DONE,
        Task.updated_at >= seven_days_ago
    ).count()

    task_counts = dict(db.session.query(Task.user_id, func.count(Task.id)).group_by(Task.user_id).all())
    completed_counts = dict(
        db.session.query(Task.user_id, func.count(Task.id))
        .filter(Task.status == STATUS_DONE)
        .group_by(Task.user_id).all()
    )

    user_stats = []
    for u in User.query.all():
        total = task_counts.get(u.id, 0)
        completed = completed_counts.get(u.id, 0)
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total)
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': status_counts[STATUS_PENDING],
            'in_progress': status_counts[STATUS_IN_PROGRESS],
            'done': status_counts[STATUS_DONE],
            'cancelled': status_counts[STATUS_CANCELLED],
        },
        'tasks_by_priority': {
            'critical': p1,
            'high': p2,
            'medium': p3,
            'low': p4,
            'minimal': p5,
        },
        'overdue': {
            'count': overdue_count,
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def build_user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404, description='Usuário não encontrado')

    user_tasks = Task.query.filter_by(user_id=user.id)

    total = user_tasks.count()
    status_counts = Task.status_counts(query=user_tasks)
    overdue = Task.overdue_count(query=user_tasks)
    high_priority = user_tasks.filter(Task.priority <= 2).count()

    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': status_counts[STATUS_DONE],
            'pending': status_counts[STATUS_PENDING],
            'in_progress': status_counts[STATUS_IN_PROGRESS],
            'cancelled': status_counts[STATUS_CANCELLED],
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(status_counts[STATUS_DONE], total)
        }
    }


def get_categories_with_task_counts(page, per_page):
    categories = Category.query.paginate(page=page, per_page=per_page, error_out=False).items

    category_ids = [c.id for c in categories]
    category_counts = dict(
        db.session.query(Task.category_id, func.count(Task.id))
        .filter(Task.category_id.in_(category_ids))
        .group_by(Task.category_id).all()
    )
    result = []
    for c in categories:
        cat_data = c.to_dict()
        cat_data['task_count'] = category_counts.get(c.id, 0)
        result.append(cat_data)
    return result


def create_category(data):
    if not data:
        abort(400, description='Dados inválidos')

    name = data.get('name')
    if not name:
        abort(400, description='Nome é obrigatório')

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', DEFAULT_COLOR)

    try:
        db.session.add(category)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao criar categoria", exc_info=e)
        abort(500, description='Erro ao criar categoria')

    return category.to_dict()


def update_category(cat_id, data):
    cat = db.session.get(Category, cat_id)
    if not cat:
        abort(404, description='Categoria não encontrada')

    if not data:
        abort(400, description='Dados inválidos')

    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    if 'color' in data:
        cat.color = data['color']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao atualizar categoria", exc_info=e)
        abort(500, description='Erro ao atualizar')

    return cat.to_dict()


def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        abort(404, description='Categoria não encontrada')

    try:
        db.session.delete(cat)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao deletar categoria", exc_info=e)
        abort(500, description='Erro ao deletar')
