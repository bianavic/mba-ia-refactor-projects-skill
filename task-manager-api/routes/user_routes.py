from flask import Blueprint, current_app, g, jsonify, request

from controllers import auth_controller, user_controller
from middleware.auth import optional_auth, owner_from_user_id, owner_or_admin, require_admin

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
@require_admin
def get_users():
    body, status = user_controller.list_users(request.args, g.current_user)
    return jsonify(body), status


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@owner_or_admin(owner_from_user_id)
def get_user(user_id):
    body, status = user_controller.get_user(user_id, request.args, g.current_user)
    return jsonify(body), status


@user_bp.route('/users', methods=['POST'])
@optional_auth
def create_user():
    body, status = user_controller.create_user(request.get_json(silent=True), g.current_user)
    return jsonify(body), status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@owner_or_admin(owner_from_user_id)
def update_user(user_id):
    body, status = user_controller.update_user(user_id, request.get_json(silent=True), g.current_user)
    return jsonify(body), status


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@owner_or_admin(owner_from_user_id)
def delete_user(user_id):
    body, status = user_controller.delete_user(user_id)
    return jsonify(body), status


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
@owner_or_admin(owner_from_user_id)
def get_user_tasks(user_id):
    body, status = user_controller.get_user_tasks(user_id, request.args)
    return jsonify(body), status


@user_bp.route('/login', methods=['POST'])
def login():
    body, status = auth_controller.login(request.get_json(silent=True), current_app.config['SECRET_KEY'])
    return jsonify(body), status
