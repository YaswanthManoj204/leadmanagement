from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from decimal import Decimal
import json

from .models import Lead, FollowUp, ActivityLog
from accounts.models import UserProfile


class LeadManagementTests(TestCase):
    def setUp(self):
        # Create Admin
        self.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='password123'
        )
        self.admin.profile.role = 'ADMIN'
        self.admin.profile.save()

        # Create Salesperson 1
        self.salesperson1 = User.objects.create_user(
            username='sales1_test',
            email='sales1@test.com',
            password='password123'
        )
        self.salesperson1.profile.role = 'SALESPERSON'
        self.salesperson1.profile.save()

        # Create Salesperson 2
        self.salesperson2 = User.objects.create_user(
            username='sales2_test',
            email='sales2@test.com',
            password='password123'
        )
        self.salesperson2.profile.role = 'SALESPERSON'
        self.salesperson2.profile.save()

        # Create a lead assigned to salesperson 1
        self.lead1 = Lead.objects.create(
            client_name='Sunil Gavaskar',
            business_name='Gavaskar Sports Media',
            location='Mumbai, Maharashtra',
            contact_number='+91 99999 11111',
            business_category='Retail & E-commerce',
            lead_source=Lead.SOURCE_MANUAL,
            lead_quality=Lead.QUALITY_WARM,
            status=Lead.STATUS_NEW_LEAD,
            assigned_to=self.salesperson1,
            created_by=self.salesperson1
        )

        self.client = Client()

    def test_requirement_1_automated_lead_capture_google_ads(self):
        """Test Requirement 1: Google Ads capture automatically assigned 'New Lead' in DB."""
        api_url = reverse('lead_capture_api')
        payload = {
            'client_name': 'Ravi Shastri',
            'business_name': 'Cricket Coaching Academy',
            'contact_number': '+91 98888 22222',
            'whatsapp_number': '+91 98888 22222',
            'email': 'ravi@cricketacademy.org',
            'location': 'New Delhi',
            'business_category': 'Education & EdTech',
            'lead_source': 'Google Ads',
            'campaign_name': 'Google Ads Q4 Search Campaign',
            'notes': 'Interested in sports academy CRM.'
        }
        response = self.client.post(
            api_url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_API_KEY=getattr(settings, 'LEAD_WEBHOOK_API_KEY', 'leadflow_secure_webhook_key_2026')
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['lead']['status'], Lead.STATUS_NEW_LEAD)

        # Verify in DB
        captured_lead = Lead.objects.get(id=data['lead']['id'])
        self.assertEqual(captured_lead.client_name, 'Ravi Shastri')
        self.assertEqual(captured_lead.lead_source, Lead.SOURCE_GOOGLE_ADS)
        self.assertEqual(captured_lead.status, Lead.STATUS_NEW_LEAD)

    def test_requirement_2_followup_logging_and_quality_update(self):
        """Test Requirement 2: Salesperson logs follow-up and updates quality & status."""
        self.client.login(username='sales1_test', password='password123')
        followup_url = reverse('log_followup', kwargs={'pk': self.lead1.pk})

        response = self.client.post(followup_url, {
            'interaction_type': 'Phone Call',
            'remarks': 'Client is very interested, discussed budget and customized packaging.',
            'status_after_followup': Lead.STATUS_IN_DISCUSSION,
            'quality_after_followup': Lead.QUALITY_HOT,
            'next_followup_date': '2026-11-25',
        })
        self.assertEqual(response.status_code, 302)

        self.lead1.refresh_from_db()
        self.assertEqual(self.lead1.status, Lead.STATUS_IN_DISCUSSION)
        self.assertEqual(self.lead1.lead_quality, Lead.QUALITY_HOT)
        self.assertEqual(str(self.lead1.next_followup_date), '2026-11-25')
        self.assertEqual(self.lead1.followups.count(), 1)

    def test_requirement_2_and_3_deal_closure_complete_business_details(self):
        """Test Requirement 2 & 3: Closing a deal records complete business details."""
        self.client.login(username='sales1_test', password='password123')
        close_deal_url = reverse('close_deal', kwargs={'pk': self.lead1.pk})

        response = self.client.post(close_deal_url, {
            'deal_value': '375000.00',
            'closed_date': '2026-11-20',
            'products_services_sold': 'CRM Enterprise 10 seats + 1 Year Maintenance',
            'contract_period': '1 Year Annual Subscription',
            'payment_terms': '50% Advance, 50% on Delivery',
            'tax_id': '27ABCDE5678F1Z9',
            'billing_address': 'Suite 401, Nariman Point, Mumbai - 400021',
            'closure_notes': 'PO received. Handed over to onboarding team.',
        })
        self.assertEqual(response.status_code, 302)

        self.lead1.refresh_from_db()
        self.assertEqual(self.lead1.status, Lead.STATUS_CLOSED_WON)
        self.assertEqual(self.lead1.deal_value, Decimal('375000.00'))
        self.assertEqual(self.lead1.contract_period, '1 Year Annual Subscription')
        self.assertEqual(self.lead1.tax_id, '27ABCDE5678F1Z9')

    def test_requirement_4_role_based_permissions(self):
        """Test Requirement 4: Salesperson only views assigned leads; Admin views all."""
        # Create lead for salesperson 2
        lead2 = Lead.objects.create(
            client_name='Kapil Dev',
            business_name='Dev Holdings',
            location='Chandigarh',
            contact_number='+91 97777 33333',
            assigned_to=self.salesperson2,
            created_by=self.salesperson2
        )

        # Salesperson 1 logs in
        self.client.login(username='sales1_test', password='password123')
        resp = self.client.get(reverse('lead_list'))
        self.assertContains(resp, 'Sunil Gavaskar')
        self.assertNotContains(resp, 'Kapil Dev') # Salesperson 1 cannot see salesperson 2's lead

        # Admin logs in
        self.client.login(username='admin_test', password='password123')
        resp_admin = self.client.get(reverse('lead_list'))
        self.assertContains(resp_admin, 'Sunil Gavaskar')
        self.assertContains(resp_admin, 'Kapil Dev') # Admin sees all leads
