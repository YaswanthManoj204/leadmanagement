import csv
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.models import User

from .models import Lead, FollowUp, ActivityLog
from .forms import LeadForm, FollowUpForm, DealClosureForm
from accounts.models import UserProfile


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_admin))


def get_user_lead_queryset(user):
    """Filter leads based on user role."""
    if user.is_superuser or (hasattr(user, 'profile') and user.profile.is_admin):
        return Lead.objects.all()
    # Salesperson sees assigned leads or leads they created
    return Lead.objects.filter(Q(assigned_to=user) | Q(created_by=user))


@login_required
def dashboard_view(request):
    user = request.user
    leads_qs = get_user_lead_queryset(user)
    today = timezone.localdate()

    # Summary KPI Stats
    total_leads = leads_qs.count()
    new_leads = leads_qs.filter(status=Lead.STATUS_NEW_LEAD).count()
    in_discussion = leads_qs.filter(status__in=[Lead.STATUS_CONTACTED, Lead.STATUS_IN_DISCUSSION]).count()
    qualified_leads = leads_qs.filter(status=Lead.STATUS_QUALIFIED).count()
    closed_won_leads = leads_qs.filter(status=Lead.STATUS_CLOSED_WON).count()
    total_revenue = leads_qs.filter(status=Lead.STATUS_CLOSED_WON).aggregate(total=Sum('deal_value'))['total'] or 0

    # Follow-up alerts
    active_leads_qs = leads_qs.exclude(status__in=[Lead.STATUS_CLOSED_WON, Lead.STATUS_CLOSED_LOST])
    due_today_count = active_leads_qs.filter(next_followup_date=today).count()
    overdue_count = active_leads_qs.filter(next_followup_date__lt=today).count()

    # Conversion Rate
    conversion_rate = round((closed_won_leads / total_leads * 100), 1) if total_leads > 0 else 0

    # Chart Data: Leads by Source
    sources_data = leads_qs.values('lead_source').annotate(count=Count('id')).order_by('-count')
    source_labels = [item['lead_source'] for item in sources_data]
    source_counts = [item['count'] for item in sources_data]

    # Chart Data: Leads by Status Pipeline
    status_data = leads_qs.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in status_data}
    pipeline_stages = [
        Lead.STATUS_NEW_LEAD,
        Lead.STATUS_CONTACTED,
        Lead.STATUS_IN_DISCUSSION,
        Lead.STATUS_QUALIFIED,
        Lead.STATUS_PROPOSAL_SENT,
        Lead.STATUS_NEGOTIATION,
        Lead.STATUS_CLOSED_WON,
        Lead.STATUS_CLOSED_LOST,
    ]
    pipeline_counts = [status_dict.get(stage, 0) for stage in pipeline_stages]

    # Chart Data: Lead Quality Breakdown
    quality_data = leads_qs.values('lead_quality').annotate(count=Count('id'))
    quality_dict = {item['lead_quality']: item['count'] for item in quality_data}
    quality_labels = ['Hot', 'Warm', 'Cold', 'Unqualified']
    quality_counts = [quality_dict.get(q, 0) for q in quality_labels]

    # Salesperson Leaderboard (for Admin)
    leaderboard = []
    if is_admin(user):
        sales_team = User.objects.filter(is_active=True).select_related('profile')
        for sp in sales_team:
            sp_leads = Lead.objects.filter(assigned_to=sp)
            sp_total = sp_leads.count()
            sp_won = sp_leads.filter(status=Lead.STATUS_CLOSED_WON).count()
            sp_revenue = sp_leads.filter(status=Lead.STATUS_CLOSED_WON).aggregate(total=Sum('deal_value'))['total'] or 0
            leaderboard.append({
                'user': sp,
                'total': sp_total,
                'won': sp_won,
                'revenue': sp_revenue,
                'conversion_rate': round((sp_won / sp_total * 100), 1) if sp_total > 0 else 0,
            })
        leaderboard.sort(key=lambda x: x['revenue'], reverse=True)

    # Today's Actionable Follow-ups
    today_followups = active_leads_qs.filter(
        Q(next_followup_date=today) | Q(next_followup_date__lt=today)
    ).order_by('next_followup_date', 'next_followup_time')[:8]

    # Recent Leads
    recent_leads = leads_qs.order_by('-created_at')[:7]

    context = {
        'total_leads': total_leads,
        'new_leads': new_leads,
        'in_discussion': in_discussion,
        'qualified_leads': qualified_leads,
        'closed_won_leads': closed_won_leads,
        'total_revenue': total_revenue,
        'due_today_count': due_today_count,
        'overdue_count': overdue_count,
        'conversion_rate': conversion_rate,
        # Charts
        'source_labels_json': json.dumps(source_labels),
        'source_counts_json': json.dumps(source_counts),
        'pipeline_stages_json': json.dumps(pipeline_stages),
        'pipeline_counts_json': json.dumps(pipeline_counts),
        'quality_labels_json': json.dumps(quality_labels),
        'quality_counts_json': json.dumps(quality_counts),
        # Lists
        'today_followups': today_followups,
        'recent_leads': recent_leads,
        'leaderboard': leaderboard,
        'is_admin_user': is_admin(user),
    }
    return render(request, 'dashboard.html', context)


@login_required
def lead_list_view(request):
    user = request.user
    leads = get_user_lead_queryset(user).select_related('assigned_to')
    today = timezone.localdate()

    # Tab Filter shortcuts
    filter_tab = request.GET.get('tab', 'all')
    if filter_tab == 'new':
        leads = leads.filter(status=Lead.STATUS_NEW_LEAD)
    elif filter_tab == 'hot':
        leads = leads.filter(lead_quality=Lead.QUALITY_HOT)
    elif filter_tab == 'today':
        leads = leads.filter(next_followup_date=today).exclude(status__in=[Lead.STATUS_CLOSED_WON, Lead.STATUS_CLOSED_LOST])
    elif filter_tab == 'overdue':
        leads = leads.filter(next_followup_date__lt=today).exclude(status__in=[Lead.STATUS_CLOSED_WON, Lead.STATUS_CLOSED_LOST])
    elif filter_tab == 'qualified':
        leads = leads.filter(status=Lead.STATUS_QUALIFIED)
    elif filter_tab == 'won':
        leads = leads.filter(status=Lead.STATUS_CLOSED_WON)

    # Detailed Filters
    q = request.GET.get('q', '').strip()
    if q:
        leads = leads.filter(
            Q(client_name__icontains=q) |
            Q(business_name__icontains=q) |
            Q(contact_number__icontains=q) |
            Q(email__icontains=q) |
            Q(location__icontains=q)
        )

    status_filter = request.GET.get('status')
    if status_filter:
        leads = leads.filter(status=status_filter)

    quality_filter = request.GET.get('quality')
    if quality_filter:
        leads = leads.filter(lead_quality=quality_filter)

    source_filter = request.GET.get('source')
    if source_filter:
        leads = leads.filter(lead_source=source_filter)

    category_filter = request.GET.get('category')
    if category_filter:
        leads = leads.filter(business_category=category_filter)

    assigned_filter = request.GET.get('assigned_to')
    if assigned_filter:
        if assigned_filter == 'unassigned':
            leads = leads.filter(assigned_to__isnull=True)
        else:
            leads = leads.filter(assigned_to_id=assigned_filter)

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['created_at', '-created_at', 'client_name', '-client_name', 'next_followup_date', '-next_followup_date', 'deal_value', '-deal_value']
    if sort_by in valid_sorts:
        leads = leads.order_by(sort_by)

    # Salespeople for filter dropdown
    salespeople = User.objects.filter(is_active=True).order_by('first_name', 'username')

    context = {
        'leads': leads,
        'filter_tab': filter_tab,
        'q': q,
        'status_filter': status_filter,
        'quality_filter': quality_filter,
        'source_filter': source_filter,
        'category_filter': category_filter,
        'assigned_filter': assigned_filter,
        'sort_by': sort_by,
        'salespeople': salespeople,
        'status_choices': Lead.STATUS_CHOICES,
        'quality_choices': Lead.QUALITY_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
        'category_choices': Lead.CATEGORY_CHOICES,
        'total_count': leads.count(),
    }
    return render(request, 'leads/lead_list.html', context)


@login_required
def lead_kanban_view(request):
    """Visual Kanban Pipeline board to organize and move leads between stages."""
    user = request.user
    leads_qs = get_user_lead_queryset(user).select_related('assigned_to')

    # Optional salesperson filter for admin
    assigned_to_id = request.GET.get('assigned_to')
    if assigned_to_id and is_admin(user):
        leads_qs = leads_qs.filter(assigned_to_id=assigned_to_id)

    stages = [
        {'id': Lead.STATUS_NEW_LEAD, 'name': 'New Lead', 'color': 'border-primary', 'badge': 'bg-primary'},
        {'id': Lead.STATUS_CONTACTED, 'name': 'Contacted', 'color': 'border-info', 'badge': 'bg-info text-dark'},
        {'id': Lead.STATUS_IN_DISCUSSION, 'name': 'In Discussion', 'color': 'border-warning', 'badge': 'bg-warning text-dark'},
        {'id': Lead.STATUS_QUALIFIED, 'name': 'Qualified', 'color': 'border-purple', 'badge': 'bg-indigo text-white'},
        {'id': Lead.STATUS_PROPOSAL_SENT, 'name': 'Proposal Sent', 'color': 'border-secondary', 'badge': 'bg-secondary'},
        {'id': Lead.STATUS_NEGOTIATION, 'name': 'Negotiation', 'color': 'border-dark', 'badge': 'bg-dark'},
        {'id': Lead.STATUS_CLOSED_WON, 'name': 'Closed Won', 'color': 'border-success', 'badge': 'bg-success'},
        {'id': Lead.STATUS_CLOSED_LOST, 'name': 'Closed Lost', 'color': 'border-danger', 'badge': 'bg-danger'},
    ]

    columns = []
    for stage in stages:
        stage_leads = leads_qs.filter(status=stage['id'])
        columns.append({
            'stage': stage,
            'leads': stage_leads,
            'count': stage_leads.count(),
        })

    salespeople = User.objects.filter(is_active=True).order_by('first_name', 'username')

    return render(request, 'leads/lead_kanban.html', {
        'columns': columns,
        'salespeople': salespeople,
        'selected_assigned': assigned_to_id,
    })


@login_required
def lead_detail_view(request, pk):
    user = request.user
    lead = get_object_or_404(get_user_lead_queryset(user), pk=pk)

    followups = lead.followups.select_related('salesperson').order_by('-interaction_date')
    activities = lead.activities.select_related('user').order_by('-timestamp')

    followup_form = FollowUpForm(initial={
        'status_after_followup': lead.status,
        'quality_after_followup': lead.lead_quality,
        'next_followup_date': lead.next_followup_date,
        'next_followup_time': lead.next_followup_time,
    })
    closure_form = DealClosureForm(instance=lead)
    salespeople = User.objects.filter(is_active=True).order_by('first_name')

    context = {
        'lead': lead,
        'followups': followups,
        'activities': activities,
        'followup_form': followup_form,
        'closure_form': closure_form,
        'salespeople': salespeople,
        'is_admin': is_admin(user),
    }
    return render(request, 'leads/lead_detail.html', context)


@login_required
def lead_create_view(request):
    """Manual Lead Entry (Requirement 1 & 3). Automatically assigned status New Lead."""
    if request.method == 'POST':
        form = LeadForm(request.POST, user=request.user)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.created_by = request.user

            # By default all new manual leads have status 'New Lead' if not specified
            if not lead.status:
                lead.status = Lead.STATUS_NEW_LEAD

            # If salesperson is creating and assigned_to wasn't chosen, default to themselves
            if not lead.assigned_to and hasattr(request.user, 'profile') and request.user.profile.is_salesperson:
                lead.assigned_to = request.user

            lead.save()

            # Log activity
            ActivityLog.objects.create(
                lead=lead,
                user=request.user,
                action="Lead Created Manually",
                details=f"Captured via Manual Lead Entry by {request.user.get_full_name() or request.user.username}. Initial status set to '{lead.status}'."
            )

            messages.success(request, f"Lead '{lead.client_name}' ({lead.business_name}) created successfully.")
            return redirect('lead_detail', pk=lead.pk)
    else:
        form = LeadForm(user=request.user, initial={
            'status': Lead.STATUS_NEW_LEAD,
            'lead_source': Lead.SOURCE_MANUAL,
            'lead_quality': Lead.QUALITY_WARM,
        })

    return render(request, 'leads/lead_form.html', {
        'form': form,
        'title': 'Capture New Lead (Manual Entry)',
        'button_text': 'Save & Capture Lead',
    })


@login_required
def lead_edit_view(request, pk):
    user = request.user
    lead = get_object_or_404(get_user_lead_queryset(user), pk=pk)

    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead, user=request.user)
        if form.is_valid():
            old_status = lead.status
            old_quality = lead.lead_quality
            updated_lead = form.save()

            changes = []
            if old_status != updated_lead.status:
                changes.append(f"Status changed from '{old_status}' to '{updated_lead.status}'")
            if old_quality != updated_lead.lead_quality:
                changes.append(f"Quality updated from '{old_quality}' to '{updated_lead.lead_quality}'")

            ActivityLog.objects.create(
                lead=updated_lead,
                user=request.user,
                action="Lead Details Updated",
                details=", ".join(changes) if changes else "Lead information edited."
            )

            messages.success(request, f"Lead '{updated_lead.client_name}' updated successfully.")
            return redirect('lead_detail', pk=updated_lead.pk)
    else:
        form = LeadForm(instance=lead, user=request.user)

    return render(request, 'leads/lead_form.html', {
        'form': form,
        'lead': lead,
        'title': f'Edit Lead: {lead.client_name}',
        'button_text': 'Update Lead Details',
    })


@login_required
def log_followup_view(request, pk):
    """Log a follow-up interaction, update lead status and quality, record next follow-up date (Requirement 2)."""
    lead = get_object_or_404(get_user_lead_queryset(request.user), pk=pk)

    if request.method == 'POST':
        form = FollowUpForm(request.POST)
        if form.is_valid():
            followup = form.save(commit=False)
            followup.lead = lead
            followup.salesperson = request.user
            followup.save()

            # Update the lead's current status, quality, and next follow-up date
            lead.status = followup.status_after_followup
            lead.lead_quality = followup.quality_after_followup
            lead.next_followup_date = followup.next_followup_date
            lead.next_followup_time = followup.next_followup_time
            lead.save()

            # Record in ActivityLog
            ActivityLog.objects.create(
                lead=lead,
                user=request.user,
                action=f"Follow-up Logged ({followup.interaction_type})",
                details=f"Status: '{lead.status}', Quality: '{lead.lead_quality}'. Remarks: {followup.remarks[:120]}..."
            )

            messages.success(request, f"Follow-up logged successfully! Lead status updated to '{lead.status}'.")
        else:
            messages.error(request, "Error logging follow-up. Please check the form fields.")

    return redirect('lead_detail', pk=lead.pk)


@login_required
def close_deal_view(request, pk):
    """Update complete business details when a deal is successfully closed (Requirement 2 & 3)."""
    lead = get_object_or_404(get_user_lead_queryset(request.user), pk=pk)

    if request.method == 'POST':
        form = DealClosureForm(request.POST, instance=lead)
        if form.is_valid():
            closed_lead = form.save(commit=False)
            closed_lead.status = Lead.STATUS_CLOSED_WON
            if not closed_lead.closed_date:
                closed_lead.closed_date = timezone.localdate()
            closed_lead.next_followup_date = None
            closed_lead.next_followup_time = None
            closed_lead.save()

            # Log follow-up history item
            FollowUp.objects.create(
                lead=closed_lead,
                salesperson=request.user,
                interaction_type='Product Demo',
                remarks=f"Deal Won & Successfully Closed! Value: {closed_lead.deal_value}. Products/Services: {closed_lead.products_services_sold}",
                status_after_followup=Lead.STATUS_CLOSED_WON,
                quality_after_followup=Lead.QUALITY_HOT
            )

            # Record in ActivityLog
            ActivityLog.objects.create(
                lead=closed_lead,
                user=request.user,
                action="🎉 Deal Successfully Closed (Won)",
                details=f"Deal Value: {closed_lead.deal_value} | Client: {closed_lead.client_name} ({closed_lead.business_name}). Complete business details recorded."
            )

            messages.success(request, f"Congratulations! Deal for '{closed_lead.business_name}' successfully closed and business details saved!")
            return redirect('lead_detail', pk=closed_lead.pk)
        else:
            messages.error(request, "Please check the deal closure form fields.")

    return redirect('lead_detail', pk=lead.pk)


@login_required
def reassign_lead_view(request, pk):
    """Reassign lead to another salesperson (Admin only or permitted)."""
    lead = get_object_or_404(Lead, pk=pk)
    if not is_admin(request.user):
        messages.error(request, "Permission denied. Only Admins can reassign leads.")
        return redirect('lead_detail', pk=lead.pk)

    if request.method == 'POST':
        salesperson_id = request.POST.get('salesperson_id')
        if salesperson_id:
            salesperson = get_object_or_404(User, pk=salesperson_id)
            prev_salesperson = lead.assigned_to.get_full_name() if lead.assigned_to else "Unassigned"
            lead.assigned_to = salesperson
            lead.save()

            ActivityLog.objects.create(
                lead=lead,
                user=request.user,
                action="Lead Reassigned",
                details=f"Reassigned from {prev_salesperson} to {salesperson.get_full_name() or salesperson.username}."
            )
            messages.success(request, f"Lead reassigned to {salesperson.get_full_name() or salesperson.username}.")
        else:
            lead.assigned_to = None
            lead.save()
            ActivityLog.objects.create(
                lead=lead,
                user=request.user,
                action="Lead Unassigned",
                details="Lead moved to unassigned pool."
            )
            messages.info(request, "Lead moved to unassigned pool.")

    return redirect('lead_detail', pk=lead.pk)


@login_required
@user_passes_test(is_admin)
def lead_delete_view(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        client_name = lead.client_name
        lead.delete()
        messages.success(request, f"Lead '{client_name}' was permanently deleted.")
        return redirect('lead_list')
    return redirect('lead_detail', pk=lead.pk)


@login_required
def update_lead_status_ajax(request):
    """AJAX endpoint for Kanban drag-and-drop or status change."""
    if request.method == 'POST':
        lead_id = request.POST.get('lead_id')
        new_status = request.POST.get('status')
        lead = get_object_or_404(get_user_lead_queryset(request.user), pk=lead_id)

        valid_statuses = [choice[0] for choice in Lead.STATUS_CHOICES]
        if new_status in valid_statuses:
            old_status = lead.status
            lead.status = new_status
            lead.save()

            ActivityLog.objects.create(
                lead=lead,
                user=request.user,
                action="Status Changed via Pipeline Board",
                details=f"Status moved from '{old_status}' to '{new_status}'"
            )
            return JsonResponse({'success': True, 'lead_id': lead.id, 'status': new_status})
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@login_required
def export_leads_csv(request):
    """Export filtered leads to CSV."""
    leads = get_user_lead_queryset(request.user).select_related('assigned_to')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="leads_export_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Client Name', 'Business Name', 'Location', 'Contact Number', 'WhatsApp Number',
        'Email', 'Business Category', 'Lead Source', 'Campaign Name', 'Lead Quality',
        'Status', 'Assigned Salesperson', 'Next Followup Date', 'Deal Value', 'Closed Date',
        'Products/Services Sold', 'Created At'
    ])

    for lead in leads:
        writer.writerow([
            lead.id,
            lead.client_name,
            lead.business_name,
            lead.location,
            lead.contact_number,
            lead.whatsapp_number or '',
            lead.email or '',
            lead.business_category,
            lead.lead_source,
            lead.campaign_name or '',
            lead.lead_quality,
            lead.status,
            lead.assigned_to.get_full_name() or lead.assigned_to.username if lead.assigned_to else 'Unassigned',
            lead.next_followup_date or '',
            lead.deal_value or '',
            lead.closed_date or '',
            lead.products_services_sold or '',
            lead.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    return response


# ==============================================================================
# LEAD CAPTURE WEBHOOK & SIMULATOR (Requirement 1: Social Media & Google Ads)
# ==============================================================================

@csrf_exempt
def lead_capture_webhook_api(request):
    """
    Centralized Webhook/API endpoint for automated lead capture:
    - Google Ads Webhook / Zapier / Make
    - Social Media Paid Campaigns (Meta Lead Ads, LinkedIn, Instagram)
    All newly captured leads are automatically recorded in the database
    and initially assigned the status 'New Lead'.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed.'}, status=405)

    # API Key check (supports header or query param)
    api_key = request.headers.get('X-API-KEY') or request.GET.get('api_key')
    expected_key = getattr(settings, 'LEAD_WEBHOOK_API_KEY', 'leadflow_secure_webhook_key_2026')
    if api_key != expected_key:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized. Invalid API Key.'}, status=401)

    # Parse JSON or Form payload
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = request.POST.dict()
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Malformed payload: {str(e)}'}, status=400)

    # Extract required fields with intelligent fallbacks
    client_name = data.get('client_name') or data.get('full_name') or data.get('name')
    contact_number = data.get('contact_number') or data.get('phone_number') or data.get('phone')
    business_name = data.get('business_name') or data.get('company_name') or data.get('company') or f"{client_name}'s Business"
    location = data.get('location') or data.get('city') or data.get('state') or 'Online / Unspecified'

    if not client_name or not contact_number:
        return JsonResponse({
            'status': 'error',
            'message': 'Missing required fields: client_name (or full_name) and contact_number (or phone_number) are required.'
        }, status=400)

    # Detect source
    raw_source = (data.get('lead_source') or data.get('source') or '').lower()
    if 'google' in raw_source:
        lead_source = Lead.SOURCE_GOOGLE_ADS
    elif any(sm in raw_source for sm in ['social', 'meta', 'facebook', 'instagram', 'linkedin', 'ads']):
        lead_source = Lead.SOURCE_SOCIAL_MEDIA
    elif 'website' in raw_source:
        lead_source = Lead.SOURCE_WEBSITE
    else:
        lead_source = data.get('lead_source', Lead.SOURCE_SOCIAL_MEDIA)

    # Create Lead
    lead = Lead.objects.create(
        client_name=client_name,
        business_name=business_name,
        location=location,
        contact_number=contact_number,
        whatsapp_number=data.get('whatsapp_number') or contact_number,
        email=data.get('email', ''),
        business_category=data.get('business_category', 'Information Technology & Software'),
        lead_source=lead_source,
        campaign_name=data.get('campaign_name') or data.get('ad_name') or data.get('utm_campaign', 'Paid Campaign Ingestion'),
        lead_quality=data.get('lead_quality', Lead.QUALITY_HOT if 'google' in lead_source.lower() else Lead.QUALITY_WARM),
        status=Lead.STATUS_NEW_LEAD, # REQUIREMENT 1: Initially assigned New Lead
        initial_notes=data.get('notes') or data.get('inquiry_details') or f"Automated capture via Webhook. Raw payload: {json.dumps(data)}"
    )

    # Auto-assign if salesperson username or email is provided in payload or round-robin
    assigned_username = data.get('assigned_to')
    if assigned_username:
        assigned_user = User.objects.filter(username=assigned_username).first()
        if assigned_user:
            lead.assigned_to = assigned_user
            lead.save()

    # Log activity
    ActivityLog.objects.create(
        lead=lead,
        user=None,
        action=f"Automated Lead Ingestion ({lead_source})",
        details=f"Received via Webhook from '{lead.campaign_name}'. Assigned initial status 'New Lead'."
    )

    return JsonResponse({
        'status': 'success',
        'message': f"Lead recorded successfully with ID {lead.id} and status '{lead.status}'.",
        'lead': {
            'id': lead.id,
            'client_name': lead.client_name,
            'business_name': lead.business_name,
            'lead_source': lead.lead_source,
            'status': lead.status,
            'created_at': lead.created_at.isoformat(),
        }
    }, status=201)


@login_required
def webhook_tester_view(request):
    """Interactive page for viewing Webhook API docs and testing Google Ads & Social Media simulation."""
    api_key = getattr(settings, 'LEAD_WEBHOOK_API_KEY', 'leadflow_secure_webhook_key_2026')
    webhook_url = request.build_absolute_uri('/api/leads/capture/')

    recent_captured = Lead.objects.filter(
        lead_source__in=[Lead.SOURCE_GOOGLE_ADS, Lead.SOURCE_SOCIAL_MEDIA]
    ).order_by('-created_at')[:10]

    return render(request, 'leads/webhook_tester.html', {
        'api_key': api_key,
        'webhook_url': webhook_url,
        'recent_captured': recent_captured,
    })
