import pytest
from werkzeug.exceptions import HTTPException

from controllers import task_controller
from database import db
from models.category import Category
from models.task import Task
from models.user import User


def _make_user(app):
    user = User(name='Ana', email='ana@example.com', role='user')
    user.set_password('1234')
    db.session.add(user)
    db.session.commit()
    return user


def _make_category(app):
    category = Category(name='Backend')
    db.session.add(category)
    db.session.commit()
    return category


def _abort_message(exc_info):
    return exc_info.value.description


class TestCreateTask:
    def test_creates_with_defaults(self, app):
        result = task_controller.create_task({'title': 'Buy milk'})

        assert result['title'] == 'Buy milk'
        assert result['status'] == 'pending'
        assert result['priority'] == 3  # DEFAULT_PRIORITY
        assert result['tags'] == []
        assert Task.query.count() == 1

    def test_empty_body_aborts_400(self, app):
        with pytest.raises(HTTPException) as exc:
            task_controller.create_task({})
        assert exc.value.code == 400
        assert _abort_message(exc) == 'Dados inválidos'

    def test_missing_title_aborts_400(self, app):
        with pytest.raises(HTTPException) as exc:
            task_controller.create_task({'description': 'no title given'})
        assert exc.value.code == 400
        assert _abort_message(exc) == 'Título é obrigatório'

    def test_title_too_short_aborts_400(self, app):
        with pytest.raises(HTTPException) as exc:
            task_controller.create_task({'title': 'ab'})
        assert exc.value.code == 400
        assert _abort_message(exc) == 'Título muito curto'

    def test_invalid_status_aborts_400(self, app):
        with pytest.raises(HTTPException) as exc:
            task_controller.create_task({'title': 'Valid title', 'status': 'bogus'})
        assert exc.value.code == 400
        assert _abort_message(exc) == 'Status inválido'

    def test_invalid_priority_aborts_400(self, app):
        with pytest.raises(HTTPException) as exc:
            task_controller.create_task({'title': 'Valid title', 'priority': 99})
        assert exc.value.code == 400
        assert _abort_message(exc) == 'Prioridade deve ser entre 1 e 5'

    def test_unknown_user_id_aborts_404(self, app):
        with pytest.raises(HTTPException) as exc:
            task_controller.create_task({'title': 'Valid title', 'user_id': 9999})
        assert exc.value.code == 404
        assert _abort_message(exc) == 'Usuário não encontrado'

    def test_unknown_category_id_aborts_404(self, app):
        with pytest.raises(HTTPException) as exc:
            task_controller.create_task({'title': 'Valid title', 'category_id': 9999})
        assert exc.value.code == 404
        assert _abort_message(exc) == 'Categoria não encontrada'

    def test_valid_user_and_category_are_linked(self, app):
        user = _make_user(app)
        category = _make_category(app)

        result = task_controller.create_task({
            'title': 'Valid title', 'user_id': user.id, 'category_id': category.id,
        })

        assert result['user_id'] == user.id
        assert result['category_id'] == category.id

    def test_bad_due_date_uses_create_specific_message(self, app):
        # AP-06 fix: the parsing logic is shared with update_task, but each
        # endpoint keeps its own original wording — this guards that split.
        with pytest.raises(HTTPException) as exc:
            task_controller.create_task({'title': 'Valid title', 'due_date': '31/12/2026'})
        assert exc.value.code == 400
        assert _abort_message(exc) == 'Formato de data inválido. Use YYYY-MM-DD'

    def test_tags_list_normalized_to_comma_string_and_back(self, app):
        result = task_controller.create_task({'title': 'Valid title', 'tags': ['a', 'b', 'c']})
        assert result['tags'] == ['a', 'b', 'c']
        assert Task.query.get(result['id']).tags == 'a,b,c'


class TestGetTask:
    def test_not_found_aborts_404(self, app):
        with pytest.raises(HTTPException) as exc:
            task_controller.get_task(9999)
        assert exc.value.code == 404

    def test_found_returns_dict(self, app):
        created = task_controller.create_task({'title': 'Valid title'})
        result = task_controller.get_task(created['id'])
        assert result['id'] == created['id']
        assert result['title'] == 'Valid title'


class TestUpdateTask:
    def test_not_found_aborts_404(self, app):
        with pytest.raises(HTTPException) as exc:
            task_controller.update_task(9999, {'title': 'x'})
        assert exc.value.code == 404

    def test_empty_body_aborts_400(self, app):
        created = task_controller.create_task({'title': 'Valid title'})
        with pytest.raises(HTTPException) as exc:
            task_controller.update_task(created['id'], None)
        assert exc.value.code == 400
        assert _abort_message(exc) == 'Dados inválidos'

    def test_partial_update_only_touches_given_fields(self, app):
        created = task_controller.create_task({'title': 'Valid title', 'priority': 2})
        result = task_controller.update_task(created['id'], {'status': 'done'})
        assert result['status'] == 'done'
        assert result['priority'] == 2  # untouched
        assert result['title'] == 'Valid title'  # untouched

    def test_bad_due_date_uses_update_specific_message(self, app):
        # Same parser as create_task, but update_task's original (shorter) message
        # must survive the AP-06 dedup — this is the one field where they differ.
        created = task_controller.create_task({'title': 'Valid title'})
        with pytest.raises(HTTPException) as exc:
            task_controller.update_task(created['id'], {'due_date': '31/12/2026'})
        assert exc.value.code == 400
        assert _abort_message(exc) == 'Formato de data inválido'

    def test_clearing_due_date_with_null(self, app):
        created = task_controller.create_task({'title': 'Valid title', 'due_date': '2026-12-01'})
        result = task_controller.update_task(created['id'], {'due_date': None})
        assert result['due_date'] is None


class TestDeleteTask:
    def test_not_found_aborts_404(self, app):
        with pytest.raises(HTTPException) as exc:
            task_controller.delete_task(9999)
        assert exc.value.code == 404

    def test_deletes_and_is_gone_after(self, app):
        created = task_controller.create_task({'title': 'Valid title'})
        task_controller.delete_task(created['id'])
        assert Task.query.get(created['id']) is None


class TestSearchAndStats:
    def test_search_filters_by_status(self, app):
        task_controller.create_task({'title': 'First task', 'status': 'pending'})
        done = task_controller.create_task({'title': 'Second task', 'status': 'in_progress'})
        task_controller.update_task(done['id'], {'status': 'done'})

        result = task_controller.search_tasks(query='', status='done', priority='', user_id='', page=1, per_page=20)

        assert len(result) == 1
        assert result[0]['status'] == 'done'

    def test_stats_counts_by_status(self, app):
        task_controller.create_task({'title': 'A task', 'status': 'pending'})
        task_controller.create_task({'title': 'B task', 'status': 'done'})

        stats = task_controller.task_stats()

        assert stats['total'] == 2
        assert stats['pending'] == 1
        assert stats['done'] == 1
