from flask import Blueprint, g, jsonify, request

from controllers import task_controller
from middleware.auth import owner_from_task_id, owner_or_admin, require_auth

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
@require_auth
def get_tasks():
    body, status = task_controller.list_tasks(request.args)
    return jsonify(body), status


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
@require_auth
def get_task(task_id):
    body, status = task_controller.get_task(task_id)
    return jsonify(body), status


@task_bp.route('/tasks', methods=['POST'])
@require_auth
def create_task():
    body, status = task_controller.create_task(request.get_json(silent=True), g.current_user)
    return jsonify(body), status


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@owner_or_admin(owner_from_task_id)
def update_task(task_id):
    body, status = task_controller.update_task(task_id, request.get_json(silent=True), g.current_user)
    return jsonify(body), status


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@owner_or_admin(owner_from_task_id)
def delete_task(task_id):
    body, status = task_controller.delete_task(task_id)
    return jsonify(body), status


@task_bp.route('/tasks/search', methods=['GET'])
@require_auth
def search_tasks():
    body, status = task_controller.search_tasks(request.args)
    return jsonify(body), status


@task_bp.route('/tasks/stats', methods=['GET'])
@require_auth
def task_stats():
    body, status = task_controller.task_stats()
    return jsonify(body), status
