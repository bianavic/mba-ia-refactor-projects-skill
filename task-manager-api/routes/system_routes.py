from flask import Blueprint, jsonify

from controllers import system_controller

system_bp = Blueprint('system', __name__)


@system_bp.route('/health')
def health():
    body, status = system_controller.health()
    return jsonify(body), status


@system_bp.route('/')
def index():
    body, status = system_controller.index()
    return jsonify(body), status
