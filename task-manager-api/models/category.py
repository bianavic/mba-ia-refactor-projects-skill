from datetime import datetime

from config import settings
from database.connection import commit, db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=settings.DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    @staticmethod
    def find(category_id):
        return db.session.get(Category, category_id)

    @staticmethod
    def list_all(pagination=None):
        query = db.select(Category).order_by(Category.id)
        if pagination:
            page, per_page = pagination
            query = query.limit(per_page).offset((page - 1) * per_page)
        return list(db.session.scalars(query))

    @staticmethod
    def count_all():
        return db.session.scalar(db.select(db.func.count(Category.id)))

    @staticmethod
    def create(fields):
        category = Category(**fields)
        db.session.add(category)
        commit('Erro ao criar categoria')
        return category

    def update(self, fields):
        for name, value in fields.items():
            setattr(self, name, value)
        commit('Erro ao atualizar')
        return self

    def delete(self):
        db.session.delete(self)
        commit('Erro ao deletar')
