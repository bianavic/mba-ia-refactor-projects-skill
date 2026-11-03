from datetime import datetime

from config import settings
from database.connection import commit, db


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(settings.MAX_TITLE_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=settings.DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=settings.DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # ---------- domain rules ----------

    def is_overdue(self, now=None):
        if not self.due_date:
            return False
        now = now or datetime.utcnow()
        return self.due_date < now and self.status not in settings.CLOSED_STATUSES

    def is_done(self):
        return self.status == settings.STATUS_DONE

    def is_high_priority(self):
        return self.priority <= settings.HIGH_PRIORITY_MAX

    def apply(self, fields):
        for name, value in fields.items():
            setattr(self, name, value)

    # ---------- serialization ----------

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(settings.TAG_SEPARATOR) if self.tags else [],
        }

    def to_detail_dict(self):
        data = self.to_dict()
        data['overdue'] = self.is_overdue()
        return data

    def to_list_dict(self):
        """GET /tasks row: detail plus the related names (relationships eager-loaded by list_all)."""
        data = self.to_detail_dict()
        data['user_name'] = self.user.name if self.user else None
        data['category_name'] = self.category.name if self.category else None
        return data

    def to_user_task_dict(self):
        """GET /users/<id>/tasks row."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    # ---------- queries ----------

    @staticmethod
    def _paginate(query, pagination):
        if pagination:
            page, per_page = pagination
            query = query.limit(per_page).offset((page - 1) * per_page)
        return query

    @staticmethod
    def find(task_id):
        return db.session.get(Task, task_id)

    @staticmethod
    def owner_of(task_id):
        """(exists, user_id) of a task — used by the owner-or-admin guard."""
        row = db.session.execute(db.select(Task.user_id).where(Task.id == task_id)).first()
        if row is None:
            return False, None
        return True, row[0]

    @staticmethod
    def list_all(pagination=None):
        query = db.select(Task).options(
            db.selectinload(Task.user), db.selectinload(Task.category)
        ).order_by(Task.id)
        return list(db.session.scalars(Task._paginate(query, pagination)))

    @staticmethod
    def list_by_user(user_id, pagination=None):
        query = db.select(Task).where(Task.user_id == user_id).order_by(Task.id)
        return list(db.session.scalars(Task._paginate(query, pagination)))

    @staticmethod
    def search(text=None, status=None, priority=None, user_id=None, pagination=None):
        query = db.select(Task)
        if text:
            pattern = f'%{text}%'  # bound as a parameter by SQLAlchemy
            query = query.where(db.or_(Task.title.like(pattern), Task.description.like(pattern)))
        if status:
            query = query.where(Task.status == status)
        if priority is not None:
            query = query.where(Task.priority == priority)
        if user_id is not None:
            query = query.where(Task.user_id == user_id)
        return list(db.session.scalars(Task._paginate(query.order_by(Task.id), pagination)))

    @staticmethod
    def list_overdue(now):
        query = db.select(Task).where(
            Task.due_date.is_not(None),
            Task.due_date < now,
            Task.status.not_in(settings.CLOSED_STATUSES),
        ).order_by(Task.id)
        return list(db.session.scalars(query))

    @staticmethod
    def count_all():
        return db.session.scalar(db.select(db.func.count(Task.id)))

    @staticmethod
    def count_by_status():
        rows = db.session.execute(db.select(Task.status, db.func.count(Task.id)).group_by(Task.status))
        counts = {status: 0 for status in settings.VALID_STATUSES}
        for status, total in rows:
            if status in counts:
                counts[status] = total
        return counts

    @staticmethod
    def count_by_priority():
        rows = db.session.execute(db.select(Task.priority, db.func.count(Task.id)).group_by(Task.priority))
        counts = {priority: 0 for priority in settings.PRIORITY_LABELS}
        for priority, total in rows:
            if priority in counts:
                counts[priority] = total
        return counts

    @staticmethod
    def count_created_since(moment):
        return db.session.scalar(db.select(db.func.count(Task.id)).where(Task.created_at >= moment))

    @staticmethod
    def count_done_updated_since(moment):
        return db.session.scalar(db.select(db.func.count(Task.id)).where(
            Task.status == settings.STATUS_DONE, Task.updated_at >= moment))

    @staticmethod
    def totals_by_user(user_ids):
        """{user_id: (total, done)} in one grouped query."""
        if not user_ids:
            return {}
        done = db.func.sum(db.case((Task.status == settings.STATUS_DONE, 1), else_=0))
        rows = db.session.execute(
            db.select(Task.user_id, db.func.count(Task.id), done)
            .where(Task.user_id.in_(user_ids)).group_by(Task.user_id))
        return {user_id: (total, int(done_count or 0)) for user_id, total, done_count in rows}

    @staticmethod
    def totals_by_category(category_ids):
        if not category_ids:
            return {}
        rows = db.session.execute(
            db.select(Task.category_id, db.func.count(Task.id))
            .where(Task.category_id.in_(category_ids)).group_by(Task.category_id))
        return dict(rows.all())

    # ---------- writes ----------

    @staticmethod
    def create(fields):
        task = Task()
        task.apply(fields)
        db.session.add(task)
        commit('Erro ao criar task')
        return task

    def update(self, fields):
        self.apply(fields)
        self.updated_at = datetime.utcnow()
        commit('Erro ao atualizar')
        return self

    def delete(self):
        db.session.delete(self)
        commit('Erro ao deletar')

    @staticmethod
    def stage_delete_by_user(user_id):
        """Mark the user's tasks for deletion; the caller commits in the same transaction."""
        for task in Task.list_by_user(user_id):
            db.session.delete(task)
