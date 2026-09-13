import logging
from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import VALID_STATUSES, MIN_TITLE_LENGTH, MAX_TITLE_LENGTH, MIN_PRIORITY, MAX_PRIORITY, utc_now

logger = logging.getLogger(__name__)

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        tasks = Task.query.options(
            joinedload(Task.user), joinedload(Task.category)
        ).paginate(page=page, per_page=per_page, error_out=False).items

        result = []
        for t in tasks:
            task_data = t.to_dict()
            task_data['user_name'] = t.user.name if t.user else None
            task_data['category_name'] = t.category.name if t.category else None
            result.append(task_data)

        return jsonify(result), 200
    except Exception as e:
        logger.error("Erro ao listar tasks", exc_info=e)
        return jsonify({'error': 'Erro interno'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify(task.to_dict()), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    title = data.get('title')
    if not title:
        return jsonify({'error': 'Título é obrigatório'}), 400

    if len(title) < MIN_TITLE_LENGTH:
        return jsonify({'error': 'Título muito curto'}), 400

    if len(title) > MAX_TITLE_LENGTH:
        return jsonify({'error': 'Título muito longo'}), 400

    description = data.get('description', '')
    status = data.get('status', 'pending')
    priority = data.get('priority', 3)
    user_id = data.get('user_id')
    category_id = data.get('category_id')
    due_date = data.get('due_date')
    tags = data.get('tags')

    if status not in VALID_STATUSES:
        return jsonify({'error': 'Status inválido'}), 400

    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400

    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

    if category_id:
        cat = Category.query.get(category_id)
        if not cat:
            return jsonify({'error': 'Categoria não encontrada'}), 404

    task = Task()
    task.title = title
    task.description = description
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    if due_date:
        try:
            task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

    if tags:
        if type(tags) == list:
            task.tags = ','.join(tags)
        else:
            task.tags = tags

    try:
        db.session.add(task)
        db.session.commit()
        logger.info(f"Task criada: {task.id} - {task.title}")
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao criar task", exc_info=e)
        return jsonify({'error': 'Erro ao criar task'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if 'title' in data:
        if len(data['title']) < MIN_TITLE_LENGTH:
            return jsonify({'error': 'Título muito curto'}), 400
        if len(data['title']) > MAX_TITLE_LENGTH:
            return jsonify({'error': 'Título muito longo'}), 400
        task.title = data['title']

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            return jsonify({'error': 'Status inválido'}), 400
        task.status = data['status']

    if 'priority' in data:
        if data['priority'] < MIN_PRIORITY or data['priority'] > MAX_PRIORITY:
            return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400
        task.priority = data['priority']

    if 'user_id' in data:
        if data['user_id']:
            user = User.query.get(data['user_id'])
            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id']:
            cat = Category.query.get(data['category_id'])
            if not cat:
                return jsonify({'error': 'Categoria não encontrada'}), 404
        task.category_id = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            try:
                task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Formato de data inválido'}), 400
        else:
            task.due_date = None

    if 'tags' in data:
        if type(data['tags']) == list:
            task.tags = ','.join(data['tags'])
        else:
            task.tags = data['tags']

    task.updated_at = utc_now()

    try:
        db.session.commit()
        logger.info(f"Task atualizada: {task.id}")
        return jsonify(task.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao atualizar task", exc_info=e)
        return jsonify({'error': 'Erro ao atualizar'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    try:
        db.session.delete(task)
        db.session.commit()
        logger.info(f"Task deletada: {task_id}")
        return jsonify({'message': 'Task deletada com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao deletar task", exc_info=e)
        return jsonify({'error': 'Erro ao deletar'}), 500


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    tasks = Task.search(
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    ).paginate(page=page, per_page=per_page, error_out=False).items

    return jsonify([t.to_dict() for t in tasks]), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(Task.get_statistics()), 200
