"""Stateless helpers with no domain meaning."""
import re

_EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
_COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    return isinstance(email, str) and bool(_EMAIL_PATTERN.match(email))


def is_valid_color(color):
    return isinstance(color, str) and bool(_COLOR_PATTERN.match(color))


def mask_email(email):
    """j***@domain — keeps the first character and the domain."""
    if not isinstance(email, str) or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"
