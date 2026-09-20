"""Regression tests for AP-08 (N+1 Query Pattern), closed in report/audit-project-3.md.

Each test proves the fix's actual advantage: the number of SQL statements issued by
the endpoint stays constant as the row count grows, instead of growing linearly (one
extra query per row) the way it did before joinedload/grouped queries were introduced.
"""
from contextlib import contextmanager

import pytest
from sqlalchemy import event

from controllers import task_controller, user_controller
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from services import report_service


@contextmanager
def count_queries():
    statements = []

    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(db.engine, 'before_cursor_execute', _before_cursor_execute)
    try:
        yield statements
    finally:
        event.remove(db.engine, 'before_cursor_execute', _before_cursor_execute)


def _make_user(name='Ana', email='ana@example.com'):
    user = User(name=name, email=email, role='user')
    user.set_password('1234')
    db.session.add(user)
    db.session.commit()
    return user


def _make_category(name='Backend'):
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return category


def _make_tasks(count, user_id=None, category_id=None):
    for i in range(count):
        task_controller.create_task({
            'title': f'Task {i}',
            'user_id': user_id,
            'category_id': category_id,
        })


class TestListTasksQueryCount:
    """controllers/task_controller.py:58-61 — joinedload(Task.user, Task.category)."""

    def test_query_count_does_not_grow_with_row_count(self, app):
        user = _make_user()
        category = _make_category()

        _make_tasks(3, user_id=user.id, category_id=category.id)
        with count_queries() as statements:
            small = task_controller.list_tasks(page=1, per_page=50)
        small_count = len(statements)

        _make_tasks(12, user_id=user.id, category_id=category.id)
        with count_queries() as statements:
            large = task_controller.list_tasks(page=1, per_page=50)
        large_count = len(statements)

        assert len(small) == 3
        assert len(large) == 15
        assert small_count == large_count
        assert large_count <= 3, (
            f'expected a constant, small query count; got {large_count} for 15 tasks — '
            'looks like the joinedload regressed back into per-row queries'
        )


class TestListUsersQueryCount:
    """controllers/user_controller.py:20-28 — one grouped count query for task_counts."""

    def test_query_count_does_not_grow_with_user_count(self, app):
        for i in range(3):
            _make_user(name=f'User {i}', email=f'user{i}@example.com')
        with count_queries() as statements:
            small = user_controller.list_users(page=1, per_page=50)
        small_count = len(statements)

        for i in range(3, 15):
            _make_user(name=f'User {i}', email=f'user{i}@example.com')
        with count_queries() as statements:
            large = user_controller.list_users(page=1, per_page=50)
        large_count = len(statements)

        assert len(small) == 3
        assert len(large) == 15
        assert small_count == large_count
        assert large_count <= 3, (
            f'expected a constant, small query count; got {large_count} for 15 users — '
            'looks like task_count regressed into a per-user query'
        )


class TestCategoriesWithTaskCountsQueryCount:
    """services/report_service.py:145-153 — one grouped count query for category_counts."""

    def test_query_count_does_not_grow_with_category_count(self, app):
        for i in range(3):
            _make_category(name=f'Category {i}')
        with count_queries() as statements:
            small = report_service.get_categories_with_task_counts(page=1, per_page=50)
        small_count = len(statements)

        for i in range(3, 15):
            _make_category(name=f'Category {i}')
        with count_queries() as statements:
            large = report_service.get_categories_with_task_counts(page=1, per_page=50)
        large_count = len(statements)

        assert len(small) == 3
        assert len(large) == 15
        assert small_count == large_count
        assert large_count <= 3, (
            f'expected a constant, small query count; got {large_count} for 15 categories — '
            'looks like task_count regressed into a per-category query'
        )
