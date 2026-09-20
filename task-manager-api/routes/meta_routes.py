from flask import Blueprint

from utils.helpers import utc_now

meta_bp = Blueprint('meta', __name__)


@meta_bp.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(utc_now())}


@meta_bp.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}
