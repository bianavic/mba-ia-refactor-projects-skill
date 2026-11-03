from flask import Blueprint, g, jsonify

from controllers import report_controller
from middleware.auth import owner_from_user_id, owner_or_admin, require_admin

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
@require_admin
def summary_report():
    body, status = report_controller.summary_report()
    return jsonify(body), status


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
@owner_or_admin(owner_from_user_id)
def user_report(user_id):
    body, status = report_controller.user_report(user_id, g.current_user)
    return jsonify(body), status
