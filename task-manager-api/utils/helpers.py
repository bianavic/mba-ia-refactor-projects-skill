from datetime import datetime, timezone


def utc_now():
    """Naive UTC timestamp - drop-in replacement for the deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def sanitize_string(s):
    if s:
        return s.strip()
    return s


def generate_id():
    import uuid
    return str(uuid.uuid4())


def is_valid_color(color):
    if color and len(color) == 7 and color[0] == '#':
        return True
    return False


VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'
