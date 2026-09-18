import pytest
from werkzeug.exceptions import HTTPException

from controllers import user_controller
from database import db
from models.task import Task
from models.user import User


def _make_user(name='Ana', email='ana@example.com', password='1234', role='user', active=True):
    user = User(name=name, email=email, role=role, active=active)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def _make_task(user_id=None, status='pending'):
    task = Task(title='Some task', status=status, user_id=user_id)
    db.session.add(task)
    db.session.commit()
    return task


def _abort_message(exc_info):
    return exc_info.value.description


class TestCreateUser:
    def test_creates_and_hides_password(self, app):
        result = user_controller.create_user({
            'name': 'Ana', 'email': 'ana@example.com', 'password': '1234',
        })
        assert result['name'] == 'Ana'
        assert 'password' not in result  # AP-04 regression guard

    def test_missing_name_aborts_400(self, app):
        with pytest.raises(HTTPException) as exc:
            user_controller.create_user({'email': 'a@a.com', 'password': '1234'})
        assert exc.value.code == 400
        assert _abort_message(exc) == 'Nome é obrigatório'

    def test_invalid_email_aborts_400(self, app):
        with pytest.raises(HTTPException) as exc:
            user_controller.create_user({'name': 'Ana', 'email': 'not-an-email', 'password': '1234'})
        assert exc.value.code == 400
        assert _abort_message(exc) == 'Email inválido'

    def test_short_password_aborts_400(self, app):
        with pytest.raises(HTTPException) as exc:
            user_controller.create_user({'name': 'Ana', 'email': 'ana@example.com', 'password': '12'})
        assert exc.value.code == 400

    def test_duplicate_email_aborts_409(self, app):
        _make_user(email='dup@example.com')
        with pytest.raises(HTTPException) as exc:
            user_controller.create_user({'name': 'Outra', 'email': 'dup@example.com', 'password': '1234'})
        assert exc.value.code == 409
        assert _abort_message(exc) == 'Email já cadastrado'

    def test_invalid_role_aborts_400(self, app):
        with pytest.raises(HTTPException) as exc:
            user_controller.create_user({'name': 'Ana', 'email': 'ana@example.com', 'password': '1234', 'role': 'root'})
        assert exc.value.code == 400


class TestListUsers:
    def test_task_counts_are_correct_without_n_plus_1(self, app):
        u1 = _make_user(email='u1@example.com')
        u2 = _make_user(email='u2@example.com')
        _make_task(user_id=u1.id)
        _make_task(user_id=u1.id)
        _make_task(user_id=u2.id)

        result = user_controller.list_users(page=1, per_page=20)

        by_id = {u['id']: u for u in result}
        assert by_id[u1.id]['task_count'] == 2
        assert by_id[u2.id]['task_count'] == 1
        assert all('password' not in u for u in result)

    def test_user_with_no_tasks_counts_zero(self, app):
        u = _make_user()
        result = user_controller.list_users(page=1, per_page=20)
        assert result[0]['task_count'] == 0

    def test_pagination_limits_results(self, app):
        for i in range(5):
            _make_user(email=f'user{i}@example.com')

        page1 = user_controller.list_users(page=1, per_page=2)
        page2 = user_controller.list_users(page=2, per_page=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert {u['id'] for u in page1}.isdisjoint({u['id'] for u in page2})


class TestUpdateUser:
    def test_not_found_aborts_404(self, app):
        with pytest.raises(HTTPException) as exc:
            user_controller.update_user(9999, {'name': 'x'})
        assert exc.value.code == 404

    def test_email_conflict_with_another_user_aborts_409(self, app):
        _make_user(email='taken@example.com')
        other = _make_user(email='other@example.com')

        with pytest.raises(HTTPException) as exc:
            user_controller.update_user(other.id, {'email': 'taken@example.com'})
        assert exc.value.code == 409

    def test_can_keep_own_email(self, app):
        u = _make_user(email='self@example.com')
        result = user_controller.update_user(u.id, {'email': 'self@example.com', 'name': 'New Name'})
        assert result['name'] == 'New Name'


class TestDeleteUser:
    def test_not_found_aborts_404(self, app):
        with pytest.raises(HTTPException) as exc:
            user_controller.delete_user(9999)
        assert exc.value.code == 404

    def test_bulk_deletes_owned_tasks(self, app):
        u = _make_user()
        _make_task(user_id=u.id)
        _make_task(user_id=u.id)

        user_controller.delete_user(u.id)

        assert User.query.get(u.id) is None
        assert Task.query.filter_by(user_id=u.id).count() == 0


class TestLogin:
    def test_wrong_password_aborts_401(self, app):
        _make_user(email='ana@example.com', password='correct-pass')
        with pytest.raises(HTTPException) as exc:
            user_controller.login({'email': 'ana@example.com', 'password': 'wrong-pass'})
        assert exc.value.code == 401

    def test_unknown_email_aborts_401(self, app):
        with pytest.raises(HTTPException) as exc:
            user_controller.login({'email': 'nobody@example.com', 'password': 'x'})
        assert exc.value.code == 401

    def test_inactive_user_aborts_403(self, app):
        _make_user(email='ana@example.com', password='1234', active=False)
        with pytest.raises(HTTPException) as exc:
            user_controller.login({'email': 'ana@example.com', 'password': '1234'})
        assert exc.value.code == 403

    def test_valid_login_returns_signed_token_without_password(self, app):
        _make_user(email='ana@example.com', password='1234')
        result = user_controller.login({'email': 'ana@example.com', 'password': '1234'})

        assert 'token' in result and result['token']
        assert 'password' not in result['user']
