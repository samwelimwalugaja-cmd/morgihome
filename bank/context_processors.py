"""Bank portal context processor - real badges (pending count)."""
from .views import _scoped_apps


def bank_badges(request):
    # Only compute for bank pages to avoid slowing other pages
    if not request.path.startswith('/bank/'):
        return {}
    try:
        from .views import PENDING_STATUSES
        qs = _scoped_apps(request)
        return {
            'bank_pending_count': qs.filter(status__in=PENDING_STATUSES).count(),
            'bank_total_count': qs.count(),
        }
    except Exception:
        return {'bank_pending_count': 0, 'bank_total_count': 0}
