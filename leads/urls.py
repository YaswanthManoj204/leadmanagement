from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Analytics
    path('', views.dashboard_view, name='dashboard'),

    # Lead Management & Views
    path('leads/', views.lead_list_view, name='lead_list'),
    path('leads/kanban/', views.lead_kanban_view, name='lead_kanban'),
    path('leads/new/', views.lead_create_view, name='lead_create'),
    path('leads/<int:pk>/', views.lead_detail_view, name='lead_detail'),
    path('leads/<int:pk>/edit/', views.lead_edit_view, name='lead_edit'),
    path('leads/<int:pk>/delete/', views.lead_delete_view, name='lead_delete'),
    path('leads/<int:pk>/followup/', views.log_followup_view, name='log_followup'),
    path('leads/<int:pk>/close-deal/', views.close_deal_view, name='close_deal'),
    path('leads/<int:pk>/reassign/', views.reassign_lead_view, name='reassign_lead'),

    # AJAX & Utilities
    path('leads/update-status-ajax/', views.update_lead_status_ajax, name='update_lead_status_ajax'),
    path('leads/export/csv/', views.export_leads_csv, name='export_leads_csv'),

    # Automated Lead Capture & Webhook API (Requirement 1: Google Ads & Social Media)
    path('api/leads/capture/', views.lead_capture_webhook_api, name='lead_capture_api'),
    path('leads/integrations/', views.webhook_tester_view, name='webhook_tester'),
]

