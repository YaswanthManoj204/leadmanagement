from django import forms
from django.contrib.auth.models import User
from .models import Lead, FollowUp


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'client_name', 'business_name', 'location',
            'contact_number', 'whatsapp_number', 'email',
            'business_category', 'lead_source', 'campaign_name',
            'lead_quality', 'status', 'assigned_to',
            'next_followup_date', 'next_followup_time', 'initial_notes'
        ]
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Rajesh Sharma'}),
            'business_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Apex Tech Solutions Pvt Ltd'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bangalore, Karnataka'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210 (Optional)'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@clientbusiness.com'}),
            'business_category': forms.Select(attrs={'class': 'form-select'}),
            'lead_source': forms.Select(attrs={'class': 'form-select'}),
            'campaign_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Google Ads Q4 B2B Campaign'}),
            'lead_quality': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'next_followup_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_followup_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'initial_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter specific customer requirements, inquiry details, or campaign details...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Populate salespeople choices
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'username')
        self.fields['assigned_to'].empty_label = "-- Unassigned (Lead Pool) --"

        # If logged-in user is a salesperson and not admin, restrict assignment or prefill
        if user and hasattr(user, 'profile') and user.profile.is_salesperson:
            # Salespersons default to themselves or cannot assign to other salespersons
            if not self.instance.pk:
                self.fields['assigned_to'].initial = user
            self.fields['assigned_to'].queryset = User.objects.filter(pk=user.pk)


class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = [
            'interaction_type', 'remarks', 'status_after_followup',
            'quality_after_followup', 'next_followup_date', 'next_followup_time'
        ]
        widgets = {
            'interaction_type': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What was discussed? Client interest level, concerns, next steps...'}),
            'status_after_followup': forms.Select(attrs={'class': 'form-select'}),
            'quality_after_followup': forms.Select(attrs={'class': 'form-select'}),
            'next_followup_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_followup_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }


class DealClosureForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'deal_value', 'closed_date', 'products_services_sold',
            'contract_period', 'payment_terms', 'billing_address',
            'tax_id', 'closure_notes'
        ]
        widgets = {
            'deal_value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'closed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'products_services_sold': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g., Enterprise CRM License (10 users) + Onboarding Support'}),
            'contract_period': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1 Year Annual Contract'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 50% Advance, 50% on Delivery / Net 30'}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Registered company billing address with Pincode'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., GSTIN / VAT Number'}),
            'closure_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Handover notes, key client contacts, billing contacts, delivery instructions...'}),
        }

