from flask import Blueprint, request, jsonify

from controllers import task_controller
from middlewares.auth import current_user, login_required

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    return jsonify(task_controller.list_tasks(page, per_page)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(task_controller.get_task(task_id)), 200


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    return jsonify(task_controller.create_task(data, actor=current_user())), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    data = request.get_json()
    return jsonify(task_controller.update_task(task_id, data, actor=current_user())), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task_controller.delete_task(task_id, actor=current_user())
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = task_controller.search_tasks(
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', type=int),
        user_id=request.args.get('user_id', type=int),
        page=page,
        per_page=per_page,
    )
    return jsonify(result), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_controller.task_stats()), 200
