from datetime import datetime

from database import db
from utils.helpers import (
    utc_now,
    calculate_percentage,
    VALID_STATUSES,
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
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
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
        return data

    @staticmethod
    def validate_status(new_status):
        return new_status in VALID_STATUSES

    @staticmethod
    def validate_priority(p):
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
        return self.due_date < utc_now() and self.status not in ('done', 'cancelled')

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
            tasks = tasks.filter(cls.priority == int(priority))
        if user_id:
            tasks = tasks.filter(cls.user_id == int(user_id))

        return tasks

    @classmethod
    def get_statistics(cls):
        total = cls.query.count()
        pending = cls.query.filter_by(status='pending').count()
        in_progress = cls.query.filter_by(status='in_progress').count()
        done = cls.query.filter_by(status='done').count()
        cancelled = cls.query.filter_by(status='cancelled').count()
        overdue = sum(1 for t in cls.query.all() if t.is_overdue())

        return {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
            'overdue': overdue,
            'completion_rate': calculate_percentage(done, total)
        }
