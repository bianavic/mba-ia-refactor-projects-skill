from flask import Blueprint, request, jsonify

from controllers import user_controller
from middlewares.auth import current_user, login_required, optional_auth

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    return jsonify(user_controller.list_users(page, per_page)), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    return jsonify(user_controller.get_user(user_id, page, per_page)), 200


@user_bp.route('/users', methods=['POST'])
@optional_auth
def create_user():
    # Public signup stays public, but an anonymous caller may only create a
    # plain 'user' account — only an admin can hand out privileged roles.
    data = request.get_json()
    return jsonify(user_controller.create_user(data, actor=current_user())), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    data = request.get_json()
    return jsonify(user_controller.update_user(user_id, data, actor=current_user())), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    user_controller.delete_user(user_id, actor=current_user())
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    return jsonify(user_controller.get_user_tasks(user_id, page, per_page)), 200


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    return jsonify(user_controller.login(data)), 200
