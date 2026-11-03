"""Health and index."""
from datetime import datetime

from config import settings


def health():
    return {'status': 'ok', 'timestamp': str(datetime.now())}, 200


def index():
    return {'message': settings.APP_NAME, 'version': settings.APP_VERSION}, 200
