from flask import Blueprint, jsonify, request

from controllers import category_controller
from middleware.auth import require_admin, require_auth

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
@require_auth
def get_categories():
    body, status = category_controller.list_categories(request.args)
    return jsonify(body), status


@category_bp.route('/categories', methods=['POST'])
@require_admin
def create_category():
    body, status = category_controller.create_category(request.get_json(silent=True))
    return jsonify(body), status


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@require_admin
def update_category(cat_id):
    body, status = category_controller.update_category(cat_id, request.get_json(silent=True))
    return jsonify(body), status


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@require_admin
def delete_category(cat_id):
    body, status = category_controller.delete_category(cat_id)
    return jsonify(body), status
