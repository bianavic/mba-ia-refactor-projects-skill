"""Application configuration: secrets and flags come from the environment; domain constants live here."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# Deployment
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
SECRET_KEY_GENERATED = not os.environ.get("SECRET_KEY")
DEBUG = _bool("APP_DEBUG", False)
HOST = os.environ.get("APP_HOST", "0.0.0.0")
PORT = int(os.environ.get("APP_PORT", "5000"))
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
TOKEN_TTL_SECONDS = int(os.environ.get("TOKEN_TTL_SECONDS", "3600"))

# Seed credentials (never literals in code)
SEED_ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD")
SEED_USER_PASSWORD = os.environ.get("SEED_USER_PASSWORD")

# Domain
APP_NAME = "Task Manager API"
APP_VERSION = "1.0"

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"
VALID_STATUSES = [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED]
CLOSED_STATUSES = [STATUS_DONE, STATUS_CANCELLED]
DEFAULT_STATUS = STATUS_PENDING

ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
VALID_ROLES = [ROLE_USER, ROLE_ADMIN, ROLE_MANAGER]
DEFAULT_ROLE = ROLE_USER

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2  # priorities 1 and 2 count as "high priority" in the user report
# Report labels for each priority value
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4
DATE_FORMAT = "%Y-%m-%d"
TAG_SEPARATOR = ","

DEFAULT_COLOR = "#000000"
RECENT_ACTIVITY_DAYS = 7

# Optional pagination
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100
