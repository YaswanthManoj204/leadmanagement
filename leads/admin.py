from django.contrib import admin
from .models import Lead, FollowUp, ActivityLog


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'business_name', 'lead_source', 'business_category', 'lead_quality', 'status', 'assigned_to', 'next_followup_date', 'created_at')
    list_filter = ('status', 'lead_quality', 'lead_source', 'business_category', 'assigned_to', 'created_at')
    search_fields = ('client_name', 'business_name', 'contact_number', 'email', 'location')
    ordering = ('-created_at',)


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('lead', 'salesperson', 'interaction_type', 'interaction_date', 'status_after_followup', 'next_followup_date')
    list_filter = ('interaction_type', 'salesperson', 'interaction_date')
    search_fields = ('lead__client_name', 'lead__business_name', 'remarks')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('lead', 'user', 'action', 'timestamp')
    list_filter = ('timestamp', 'action')
    search_fields = ('lead__client_name', 'action', 'details')
