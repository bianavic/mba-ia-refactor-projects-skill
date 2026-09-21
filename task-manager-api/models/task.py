from datetime import datetime

from database import db
from utils.helpers import (
    utc_now,
    calculate_percentage,
    VALID_STATUSES,
    CLOSED_STATUSES,
    STATUS_PENDING,
    STATUS_IN_PROGRESS,
    STATUS_DONE,
    STATUS_CANCELLED,
    MIN_PRIORITY,
    MAX_PRIORITY,
    MIN_TITLE_LENGTH,
    MAX_TITLE_LENGTH,
    DEFAULT_PRIORITY,
)

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self, exclude=None):
        data = {}
        data['id'] = self.id
        data['title'] = self.title
        data['description'] = self.description
        data['status'] = self.status
        data['priority'] = self.priority
        data['user_id'] = self.user_id
        data['category_id'] = self.category_id
        data['created_at'] = str(self.created_at)
        data['updated_at'] = str(self.updated_at)
        data['due_date'] = str(self.due_date) if self.due_date else None
        data['tags'] = self.tags.split(',') if self.tags else []
        data['overdue'] = self.is_overdue()
        if exclude:
            for field in exclude:
                data.pop(field, None)
        return data

    @staticmethod
    def validate_status(new_status):
        return new_status in VALID_STATUSES

    @staticmethod
    def validate_priority(p):
        if isinstance(p, bool):
            return False
        if not isinstance(p, int):
            try:
                p = int(p)
            except (TypeError, ValueError):
                return False
        return MIN_PRIORITY <= p <= MAX_PRIORITY

    @staticmethod
    def title_error(title):
        """Return an error message for an invalid title length, or None if it's valid."""
        if len(title) < MIN_TITLE_LENGTH:
            return 'Título muito curto'
        if len(title) > MAX_TITLE_LENGTH:
            return 'Título muito longo'
        return None

    @staticmethod
    def parse_due_date(due_date_str):
        return datetime.strptime(due_date_str, '%Y-%m-%d')

    @staticmethod
    def normalize_tags(tags):
        if isinstance(tags, list):
            return ','.join(tags)
        return tags

    def is_overdue(self):
        if not self.due_date:
            return False
        return self.due_date < utc_now() and self.status not in CLOSED_STATUSES

    @classmethod
    def search(cls, query=None, status=None, priority=None, user_id=None):
        tasks = cls.query

        if query:
            tasks = tasks.filter(
                db.or_(
                    cls.title.like(f'%{query}%'),
                    cls.description.like(f'%{query}%')
                )
            )
        if status:
            tasks = tasks.filter(cls.status == status)
        if priority:
            tasks = tasks.filter(cls.priority == priority)
        if user_id:
            tasks = tasks.filter(cls.user_id == user_id)

        return tasks

    @classmethod
    def status_counts(cls, query=None):
        """Return {status: count} for every VALID_STATUSES value via one grouped query,
        optionally scoped to `query` (e.g. a query already filtered by user_id)."""
        base = query if query is not None else cls.query
        counts = dict(
            base.with_entities(cls.status, db.func.count(cls.id))
            .group_by(cls.status)
            .all()
        )
        return {status: counts.get(status, 0) for status in VALID_STATUSES}

    @classmethod
    def overdue_query(cls, query=None):
        """Return the (optionally scoped) query filtered down to overdue tasks, expressed
        as a SQL predicate rather than hydrating rows to check in Python."""
        base = query if query is not None else cls.query
        return base.filter(
            cls.due_date.isnot(None),
            cls.due_date < utc_now(),
            cls.status.notin_(CLOSED_STATUSES),
        )

    @classmethod
    def overdue_count(cls, query=None):
        return cls.overdue_query(query).count()

    @classmethod
    def get_statistics(cls):
        total = cls.query.count()
        counts = cls.status_counts()
        overdue = cls.overdue_count()

        return {
            'total': total,
            'pending': counts[STATUS_PENDING],
            'in_progress': counts[STATUS_IN_PROGRESS],
            'done': counts[STATUS_DONE],
            'cancelled': counts[STATUS_CANCELLED],
            'overdue': overdue,
            'completion_rate': calculate_percentage(counts[STATUS_DONE], total)
        }
