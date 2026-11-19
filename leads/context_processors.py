from django.utils import timezone
from .models import Lead


def lead_counts_processor(request):
    if not request.user.is_authenticated:
        return {}

    today = timezone.localdate()
    qs = Lead.objects.all()

    # Salesperson permission filter
    if hasattr(request.user, 'profile') and request.user.profile.is_salesperson:
        qs = qs.filter(assigned_to=request.user)

    new_leads_count = qs.filter(status=Lead.STATUS_NEW_LEAD).count()
    due_today_count = qs.filter(
        next_followup_date=today
    ).exclude(status__in=[Lead.STATUS_CLOSED_WON, Lead.STATUS_CLOSED_LOST]).count()
    overdue_count = qs.filter(
        next_followup_date__lt=today
    ).exclude(status__in=[Lead.STATUS_CLOSED_WON, Lead.STATUS_CLOSED_LOST]).count()

    return {
        'nav_new_leads_count': new_leads_count,
        'nav_due_today_count': due_today_count,
        'nav_overdue_count': overdue_count,
    }

