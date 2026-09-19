from flask import Blueprint, request, jsonify

from services import report_service

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(report_service.build_summary_report()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    return jsonify(report_service.build_user_report(user_id)), 200


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    return jsonify(report_service.get_categories_with_task_counts(page, per_page)), 200


@report_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    return jsonify(report_service.create_category(data)), 201


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    data = request.get_json()
    return jsonify(report_service.update_category(cat_id, data)), 200


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    report_service.delete_category(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
