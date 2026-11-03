"""Report request flow."""
from services import report_service


def summary_report():
    return report_service.summary(), 200


def user_report(user_id, viewer):
    user, statistics = report_service.user_report(user_id)
    public = user.to_dict(full_email=viewer is not None and viewer.id == user.id)
    return {
        'user': {'id': public['id'], 'name': public['name'], 'email': public['email']},
        'statistics': statistics,
    }, 200
