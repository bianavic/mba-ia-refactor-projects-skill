"""Category listing with the number of tasks in each category."""
from models.category import Category
from models.task import Task


def list_categories_with_task_counts(pagination=None):
    categories = Category.list_all(pagination)
    totals = Task.totals_by_category([category.id for category in categories])
    return [(category, totals.get(category.id, 0)) for category in categories]
