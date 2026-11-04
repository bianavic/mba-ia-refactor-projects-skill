"""Script para popular o banco com dados iniciais"""
import sys

from app import app
from config import settings
from database.connection import db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import datetime, timedelta

def seed_data():
    with app.app_context():

        db.session.execute(db.delete(Task))
        db.session.execute(db.delete(User))
        db.session.execute(db.delete(Category))
        db.session.commit()

        # Passwords come from the environment (SEED_ADMIN_PASSWORD / SEED_USER_PASSWORD);
        # an account without a password is not created.
        def seed_user(name, email, password, role):
            if not password:
                print(f"  {role} account skipped: password env var not set", file=sys.stderr)
                return None
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            return user

        u1 = seed_user('João Silva', 'joao@email.com', settings.SEED_ADMIN_PASSWORD, settings.ROLE_ADMIN)
        u2 = seed_user('Maria Santos', 'maria@email.com', settings.SEED_USER_PASSWORD, settings.ROLE_USER)
        u3 = seed_user('Pedro Oliveira', 'pedro@email.com', settings.SEED_USER_PASSWORD, settings.ROLE_MANAGER)

        db.session.commit()

        def user_id(user):
            return user.id if user else None

        c1 = Category()
        c1.name = 'Backend'
        c1.description = 'Tarefas de backend'
        c1.color = '#3498db'
        db.session.add(c1)

        c2 = Category()
        c2.name = 'Frontend'
        c2.description = 'Tarefas de frontend'
        c2.color = '#2ecc71'
        db.session.add(c2)

        c3 = Category()
        c3.name = 'DevOps'
        c3.description = 'Tarefas de infraestrutura'
        c3.color = '#e74c3c'
        db.session.add(c3)

        c4 = Category()
        c4.name = 'Bug'
        c4.description = 'Correção de bugs'
        c4.color = '#e67e22'
        db.session.add(c4)

        db.session.commit()

        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': user_id(u1), 'category_id': c1.id, 'due_date': datetime.utcnow() - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': user_id(u2), 'category_id': c2.id, 'due_date': datetime.utcnow() + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': user_id(u3), 'category_id': c3.id, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': user_id(u1), 'category_id': c4.id, 'due_date': datetime.utcnow() - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': user_id(u1), 'category_id': c1.id, 'due_date': datetime.utcnow() + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': user_id(u2), 'category_id': c1.id},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': user_id(u3), 'category_id': c1.id},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': user_id(u2), 'category_id': c1.id, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': user_id(u3), 'category_id': c3.id, 'due_date': datetime.utcnow() + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': user_id(u1), 'category_id': c1.id, 'tags': 'improvement,validation'},
        ]

        for td in tasks_data:
            t = Task()
            t.title = td['title']
            t.description = td['description']
            t.status = td['status']
            t.priority = td['priority']
            t.user_id = td['user_id']
            t.category_id = td['category_id']
            if 'due_date' in td:
                t.due_date = td['due_date']
            if 'tags' in td:
                t.tags = td['tags']
            db.session.add(t)

        db.session.commit()
        print("Seed concluído com sucesso!")
        print(f"  {User.count_all()} usuários")
        print(f"  {Category.count_all()} categorias")
        print(f"  {Task.count_all()} tasks")

if __name__ == '__main__':
    seed_data()
