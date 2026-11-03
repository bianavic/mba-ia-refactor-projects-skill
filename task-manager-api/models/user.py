from datetime import datetime

from config import settings
from database.connection import commit, db
from utils.helpers import mask_email
from utils.security import hash_password, is_modern_hash, verify_password


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=settings.DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, full_email=False):
        """Public fields only — never the password hash. The full email goes only to its subject."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email if full_email else mask_email(self.email),
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, pwd):
        self.password = hash_password(pwd)

    def check_password(self, pwd):
        return verify_password(self.password, pwd)

    def needs_rehash(self):
        return not is_modern_hash(self.password)

    def is_admin(self):
        return self.role == settings.ROLE_ADMIN

    # ---------- queries ----------

    @staticmethod
    def find(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def find_by_email(email):
        return db.session.scalars(db.select(User).where(User.email == email)).first()

    @staticmethod
    def list_all(pagination=None):
        query = db.select(User).order_by(User.id)
        if pagination:
            page, per_page = pagination
            query = query.limit(per_page).offset((page - 1) * per_page)
        return list(db.session.scalars(query))

    @staticmethod
    def count_all():
        return db.session.scalar(db.select(db.func.count(User.id)))

    # ---------- writes ----------

    @staticmethod
    def create(name, email, password, role):
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        commit('Erro ao criar usuário')
        return user

    def update(self, fields):
        password = fields.pop('password', None)
        for name, value in fields.items():
            setattr(self, name, value)
        if password is not None:
            self.set_password(password)
        commit('Erro ao atualizar')
        return self

    def upgrade_password_hash(self, pwd):
        """Replace a legacy MD5 hash after a successful login."""
        self.set_password(pwd)
        commit('Erro ao atualizar')

    def stage_delete(self):
        db.session.delete(self)

    @staticmethod
    def commit_deletion():
        commit('Erro ao deletar')
