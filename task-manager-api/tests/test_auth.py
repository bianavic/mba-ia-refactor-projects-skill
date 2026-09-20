import pytest
from werkzeug.exceptions import HTTPException

from controllers import task_controller, user_controller
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from services import token_service
from services.token_service import InvalidToken


def _make_user(name='Ana', email='ana@example.com', role='user', active=True):
    user = User(name=name, email=email, role=role, active=active)
    user.set_password('1234')
    db.session.add(user)
    db.session.commit()
    return user


def _make_task(owner_id=None):
    task = Task(title='Some task', user_id=owner_id)
    db.session.add(task)
    db.session.commit()
    return task


class TestTokenService:
    def test_round_trip(self, app):
        token = token_service.issue_token(42)
        assert token_service.read_token(token) == 42

    def test_missing_token_rejected(self, app):
        with pytest.raises(InvalidToken):
            token_service.read_token(None)

    def test_tampered_token_rejected(self, app):
        token = token_service.issue_token(42)
        with pytest.raises(InvalidToken):
            token_service.read_token(token + 'x')

    def test_token_signed_with_another_key_rejected(self, app):
        """A token forged with a different SECRET_KEY must not be accepted."""
        from itsdangerous import URLSafeTimedSerializer

        forged = URLSafeTimedSerializer(
            'dev-secret-change-in-production', salt=token_service.TOKEN_SALT
        ).dumps({'user_id': 1})

        with pytest.raises(InvalidToken):
            token_service.read_token(forged)

    def test_expired_token_rejected(self, app):
        app.config['TOKEN_MAX_AGE_SECONDS'] = -1
        token = token_service.issue_token(42)
        with pytest.raises(InvalidToken) as exc:
            token_service.read_token(token)
        assert 'expirado' in str(exc.value)


class TestGuard:
    """The guard revalidates the subject on every request, not just the signature."""

    def test_valid_token_resolves_user(self, app):
        user = _make_user()
        token = token_service.issue_token(user.id)
        with app.test_request_context(headers={'Authorization': f'Bearer {token}'}):
            from middlewares.auth import _resolve_current_user
            assert _resolve_current_user().id == user.id

    def test_token_of_deleted_user_rejected(self, app):
        user = _make_user()
        token = token_service.issue_token(user.id)
        db.session.delete(user)
        db.session.commit()

        with app.test_request_context(headers={'Authorization': f'Bearer {token}'}):
            from middlewares.auth import _resolve_current_user
            with pytest.raises(HTTPException) as exc:
                _resolve_current_user()
            assert exc.value.code == 401

    def test_token_of_deactivated_user_rejected(self, app):
        user = _make_user(active=False)
        token = token_service.issue_token(user.id)

        with app.test_request_context(headers={'Authorization': f'Bearer {token}'}):
            from middlewares.auth import _resolve_current_user
            with pytest.raises(HTTPException) as exc:
                _resolve_current_user()
            assert exc.value.code == 403

    def test_non_bearer_header_rejected(self, app):
        with app.test_request_context(headers={'Authorization': 'Basic abc'}):
            from middlewares.auth import _resolve_current_user
            with pytest.raises(HTTPException) as exc:
                _resolve_current_user()
            assert exc.value.code == 401


class TestUserAuthorization:
    def test_user_can_update_self(self, app):
        user = _make_user()
        result = user_controller.update_user(user.id, {'name': 'Nova'}, actor=user)
        assert result['name'] == 'Nova'

    def test_user_cannot_update_someone_else(self, app):
        ana = _make_user()
        bob = _make_user(name='Bob', email='bob@example.com')
        with pytest.raises(HTTPException) as exc:
            user_controller.update_user(bob.id, {'name': 'Hacked'}, actor=ana)
        assert exc.value.code == 403

    def test_admin_can_update_anyone(self, app):
        admin = _make_user(name='Admin', email='admin@example.com', role='admin')
        bob = _make_user(name='Bob', email='bob@example.com')
        result = user_controller.update_user(bob.id, {'name': 'Fixed'}, actor=admin)
        assert result['name'] == 'Fixed'

    def test_user_cannot_delete_someone_else(self, app):
        ana = _make_user()
        bob = _make_user(name='Bob', email='bob@example.com')
        with pytest.raises(HTTPException) as exc:
            user_controller.delete_user(bob.id, actor=ana)
        assert exc.value.code == 403

    def test_user_cannot_promote_self_to_admin(self, app):
        user = _make_user()
        with pytest.raises(HTTPException) as exc:
            user_controller.update_user(user.id, {'role': 'admin'}, actor=user)
        assert exc.value.code == 403

    def test_anonymous_signup_cannot_choose_admin_role(self, app):
        with pytest.raises(HTTPException) as exc:
            user_controller.create_user(
                {'name': 'Mallory', 'email': 'm@example.com', 'password': '1234', 'role': 'admin'},
                actor=None,
            )
        assert exc.value.code == 403

    def test_anonymous_signup_as_plain_user_allowed(self, app):
        result = user_controller.create_user(
            {'name': 'Ana', 'email': 'ana@example.com', 'password': '1234'}, actor=None
        )
        assert result['role'] == 'user'


class TestTaskAuthorization:
    def test_owner_can_update_own_task(self, app):
        ana = _make_user()
        task = _make_task(owner_id=ana.id)
        result = task_controller.update_task(task.id, {'title': 'Renamed'}, actor=ana)
        assert result['title'] == 'Renamed'

    def test_user_cannot_update_someone_elses_task(self, app):
        ana = _make_user()
        bob = _make_user(name='Bob', email='bob@example.com')
        task = _make_task(owner_id=bob.id)
        with pytest.raises(HTTPException) as exc:
            task_controller.update_task(task.id, {'title': 'Hacked'}, actor=ana)
        assert exc.value.code == 403

    def test_user_cannot_delete_someone_elses_task(self, app):
        ana = _make_user()
        bob = _make_user(name='Bob', email='bob@example.com')
        task = _make_task(owner_id=bob.id)
        with pytest.raises(HTTPException) as exc:
            task_controller.delete_task(task.id, actor=ana)
        assert exc.value.code == 403

    def test_admin_can_delete_any_task(self, app):
        admin = _make_user(name='Admin', email='admin@example.com', role='admin')
        bob = _make_user(name='Bob', email='bob@example.com')
        task = _make_task(owner_id=bob.id)
        task_controller.delete_task(task.id, actor=admin)
        assert db.session.get(Task, task.id) is None

    def test_user_cannot_create_task_for_someone_else(self, app):
        ana = _make_user()
        bob = _make_user(name='Bob', email='bob@example.com')
        with pytest.raises(HTTPException) as exc:
            task_controller.create_task({'title': 'Not mine', 'user_id': bob.id}, actor=ana)
        assert exc.value.code == 403

    def test_user_can_create_own_task(self, app):
        ana = _make_user()
        result = task_controller.create_task({'title': 'Mine', 'user_id': ana.id}, actor=ana)
        assert result['user_id'] == ana.id


class TestRouteEnforcement:
    """End-to-end through the HTTP layer: the guard is actually wired to the routes."""

    def test_write_without_token_is_401(self, app):
        client = app.test_client()
        assert client.post('/tasks', json={'title': 'Anon'}).status_code == 401
        assert client.delete('/tasks/1').status_code == 401
        assert client.put('/users/1', json={'name': 'x'}).status_code == 401
        assert client.delete('/users/1').status_code == 401

    def test_reads_stay_public(self, app):
        client = app.test_client()
        assert client.get('/tasks').status_code == 200
        assert client.get('/users').status_code == 200
        assert client.get('/categories').status_code == 200
        assert client.get('/reports/summary').status_code == 200

    def test_write_with_token_succeeds(self, app):
        user = _make_user()
        token = token_service.issue_token(user.id)
        client = app.test_client()
        response = client.post(
            '/tasks',
            json={'title': 'Authenticated task'},
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == 201

    def test_plain_user_cannot_write_categories(self, app):
        user = _make_user()
        token = token_service.issue_token(user.id)
        client = app.test_client()
        response = client.post(
            '/categories', json={'name': 'QA'},
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == 403

    def test_manager_can_write_categories(self, app):
        manager = _make_user(name='Mng', email='mng@example.com', role='manager')
        token = token_service.issue_token(manager.id)
        client = app.test_client()
        response = client.post(
            '/categories', json={'name': 'QA'},
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == 201
        assert Category.query.filter_by(name='QA').count() == 1
