import os
import django
from decimal import Decimal
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lead_manager.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import UserProfile
from leads.models import Lead, FollowUp, ActivityLog


def seed_database():
    print("🌱 Starting LeadFlow CRM Database Seeding...")

    # 1. Create or Get Admin User
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@leadflow.local',
            'first_name': 'Super',
            'last_name': 'Admin',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    admin_user.set_password('admin123')
    admin_user.save()
    admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
    admin_profile.role = 'ADMIN'
    admin_profile.designation = 'Managing Director & Head of Sales'
    admin_profile.avatar_color = '#dc2626'
    admin_profile.phone = '+91 98000 11111'
    admin_profile.save()
    print("  ✅ Admin user verified: admin / admin123")

    # 2. Create Salespeople
    sales_reps_data = [
        ('vikram_sales', 'Vikram', 'Malhotra', 'vikram@company.com', '+91 98222 33441', 'Senior Sales Specialist', '#2563eb', 1200000.00),
        ('ananya_leads', 'Ananya', 'Iyer', 'ananya@company.com', '+91 98333 44552', 'Key Account Executive', '#7c3aed', 1000000.00),
        ('rahul_biz', 'Rahul', 'Deshmukh', 'rahul@company.com', '+91 98444 55663', 'Business Development Rep', '#059669', 800000.00),
    ]

    salespeople = []
    for uname, fname, lname, email, phone, desig, color, target in sales_reps_data:
        sp, _ = User.objects.get_or_create(
            username=uname,
            defaults={
                'email': email,
                'first_name': fname,
                'last_name': lname,
            }
        )
        sp.set_password('sales123')
        sp.save()
        prof, _ = UserProfile.objects.get_or_create(user=sp)
        prof.role = 'SALESPERSON'
        prof.phone = phone
        prof.designation = desig
        prof.avatar_color = color
        prof.monthly_target = Decimal(str(target))
        prof.save()
        salespeople.append(sp)
        print(f"  ✅ Salesperson verified: {uname} / sales123")

    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)

    # 3. Clear existing demo leads if re-running
    Lead.objects.all().delete()
    print("  🧹 Resetting leads...")

    # 4. Realistic Sample Leads
    leads_data = [
        # Lead 1: Google Ads - Closed Won with complete business details
        {
            'client_name': 'Aarav Singhania',
            'business_name': 'Singhania Cloud Solutions Pvt Ltd',
            'location': 'Bengaluru, Karnataka',
            'contact_number': '+91 98765 11001',
            'whatsapp_number': '+91 98765 11001',
            'email': 'aarav@singhaniacloud.in',
            'business_category': 'Information Technology & Software',
            'lead_source': Lead.SOURCE_GOOGLE_ADS,
            'campaign_name': 'Google Ads B2B Tech High-Intent Q4',
            'lead_quality': Lead.QUALITY_HOT,
            'status': Lead.STATUS_CLOSED_WON,
            'assigned_to': salespeople[0],
            'deal_value': Decimal('450000.00'),
            'closed_date': today - timedelta(days=3),
            'products_services_sold': 'Enterprise SaaS CRM License (25 seats) + Custom API Integrations & Dedicated Support',
            'contract_period': '1 Year Annual Agreement',
            'payment_terms': '50% Upfront, 50% Net 30 after deployment',
            'billing_address': 'Tower B, 7th Floor, RMZ Ecoworld, Outer Ring Road, Bengaluru - 560103',
            'tax_id': '29ABCDE1234F1Z5 (GSTIN)',
            'closure_notes': 'Key contact is CFO Mr. Sharma for billing. Kickoff meeting scheduled for Monday.',
            'initial_notes': 'Inbound search ad inquiry looking for scalable lead automation for tech sales reps.',
            'followups': [
                ('Phone Call', timezone.now() - timedelta(days=14), 'Initial introduction call. Understood team size and requirements.', 'Contacted', 'Warm', today - timedelta(days=10)),
                ('Online Meeting (Zoom/Meet)', timezone.now() - timedelta(days=10), 'Conducted detailed product walkthrough. Client highly impressed with WhatsApp integration.', 'In Discussion', 'Hot', today - timedelta(days=7)),
                ('Proposal Shared', timezone.now() - timedelta(days=7), 'Sent customized commercial quote with tiered volume pricing.', 'Proposal Sent', 'Hot', today - timedelta(days=4)),
                ('In-person Meeting', timezone.now() - timedelta(days=3), 'Final negotiation and PO signing with procurement.', 'Closed Won', 'Hot', None),
            ]
        },

        # Lead 2: Social Media Paid Campaign - Hot Quality, Follow-up Due Today!
        {
            'client_name': 'Priya Sundaram',
            'business_name': 'MedPulse Healthcare Clinics',
            'location': 'Chennai, Tamil Nadu',
            'contact_number': '+91 98111 22334',
            'whatsapp_number': '+91 98111 22334',
            'email': 'priya.sundaram@medpulse.org',
            'business_category': 'Healthcare & Pharmaceuticals',
            'lead_source': Lead.SOURCE_SOCIAL_MEDIA,
            'campaign_name': 'Meta Facebook Lead Gen - Healthcare Clinics Campaign',
            'lead_quality': Lead.QUALITY_HOT,
            'status': Lead.STATUS_QUALIFIED,
            'assigned_to': salespeople[1],
            'next_followup_date': today,
            'initial_notes': 'Interested in patient appointment lead tracking across 5 branch clinics.',
            'followups': [
                ('Phone Call', timezone.now() - timedelta(days=2), 'Spoke with Dr. Priya. She wants a quick demo for clinic front desk managers.', 'Contacted', 'Hot', today),
                ('WhatsApp Message', timezone.now() - timedelta(days=1), 'Shared feature sheet and demo video link on WhatsApp.', 'Qualified', 'Hot', today),
            ]
        },

        # Lead 3: Google Ads - Proposal Sent, Overdue Follow-up alert
        {
            'client_name': 'Rameshwar Kulkarni',
            'business_name': 'Kulkarni Builders & Urban Infra',
            'location': 'Pune, Maharashtra',
            'contact_number': '+91 98222 77889',
            'whatsapp_number': '+91 98222 77889',
            'email': 'rameshwar@kulkarnibuilders.com',
            'business_category': 'Real Estate & Construction',
            'lead_source': Lead.SOURCE_GOOGLE_ADS,
            'campaign_name': 'Google Ads - Commercial Real Estate Leads',
            'lead_quality': Lead.QUALITY_WARM,
            'status': Lead.STATUS_PROPOSAL_SENT,
            'assigned_to': salespeople[0],
            'next_followup_date': yesterday,
            'initial_notes': 'Needs lead capture for luxury residential township project in Pune.',
            'followups': [
                ('Phone Call', timezone.now() - timedelta(days=6), 'Discovery call regarding sales team workflows and site visit tracking.', 'In Discussion', 'Warm', today - timedelta(days=4)),
                ('Proposal Shared', timezone.now() - timedelta(days=4), 'Shared formal proposal for ₹2,80,000 package.', 'Proposal Sent', 'Warm', yesterday),
            ]
        },

        # Lead 4: Social Media Paid Campaign - Brand New Lead (Requirement 1: Status = New Lead)
        {
            'client_name': 'Deepak Verma',
            'business_name': 'Verma Agro Organics',
            'location': 'Indore, Madhya Pradesh',
            'contact_number': '+91 98999 55667',
            'whatsapp_number': '+91 98999 55667',
            'email': 'deepak@vermaorganics.com',
            'business_category': 'Retail & E-commerce',
            'lead_source': Lead.SOURCE_SOCIAL_MEDIA,
            'campaign_name': 'Instagram Story Lead Form - D2C Brands',
            'lead_quality': Lead.QUALITY_WARM,
            'status': Lead.STATUS_NEW_LEAD, # REQUIREMENT 1
            'assigned_to': salespeople[2],
            'next_followup_date': today,
            'initial_notes': 'Captured via Instagram Lead Form. Expanding wholesale distribution network across Central India.',
            'followups': []
        },

        # Lead 5: Manual Lead Entry - Negotiation Stage
        {
            'client_name': 'Sanjay Mehta',
            'business_name': 'Apex Logistics & Freight Hub',
            'location': 'Mumbai, Maharashtra',
            'contact_number': '+91 98666 44332',
            'whatsapp_number': '+91 98666 44332',
            'email': 'sanjay@apexlogistics.in',
            'business_category': 'Manufacturing & Industrial',
            'lead_source': Lead.SOURCE_MANUAL,
            'campaign_name': 'Industry Expo 2026 Direct Contact',
            'lead_quality': Lead.QUALITY_HOT,
            'status': Lead.STATUS_NEGOTIATION,
            'assigned_to': salespeople[1],
            'next_followup_date': tomorrow,
            'initial_notes': 'Met at National Logistics Expo. Looking to streamline B2B quotes.',
            'followups': [
                ('In-person Meeting', timezone.now() - timedelta(days=8), 'Met at expo stall. Exchanged business cards.', 'Contacted', 'Warm', today - timedelta(days=5)),
                ('Product Demo', timezone.now() - timedelta(days=5), 'Demonstrated dashboard, reports and mobile accessibility.', 'Qualified', 'Hot', today - timedelta(days=2)),
                ('Phone Call', timezone.now() - timedelta(days=2), 'Discussed custom pricing discount for 2-year commitment.', 'Negotiation', 'Hot', tomorrow),
            ]
        },

        # Lead 6: Manual Entry - Closed Won (Another large deal)
        {
            'client_name': 'Meera Nambiar',
            'business_name': 'EduSpark Learning Academy',
            'location': 'Kochi, Kerala',
            'contact_number': '+91 98450 99881',
            'whatsapp_number': '+91 98450 99881',
            'email': 'meera@eduspark.edu.in',
            'business_category': 'Education & EdTech',
            'lead_source': Lead.SOURCE_MANUAL,
            'campaign_name': 'Management Referral',
            'lead_quality': Lead.QUALITY_HOT,
            'status': Lead.STATUS_CLOSED_WON,
            'assigned_to': salespeople[2],
            'deal_value': Decimal('320000.00'),
            'closed_date': today - timedelta(days=5),
            'products_services_sold': 'Student Admission Lead Management CRM Suite + Multi-counselor Access',
            'contract_period': '1 Year Full Academic Year',
            'payment_terms': '100% Full Payment upon agreement',
            'billing_address': 'Plot 44, InfoPark Expressway, Kakkanad, Kochi, Kerala - 682030',
            'tax_id': '32AABCE9876K1ZQ',
            'closure_notes': 'Payment received via RTGS. Training session scheduled with counselors.',
            'initial_notes': 'Referred by Board Member. Required student admission funnel automation.',
            'followups': [
                ('Product Demo', timezone.now() - timedelta(days=12), 'Demo shown to admissions director.', 'Qualified', 'Hot', today - timedelta(days=8)),
                ('In-person Meeting', timezone.now() - timedelta(days=5), 'Contract signed.', 'Closed Won', 'Hot', None),
            ]
        },

        # Lead 7: Google Ads - New Lead (Unassigned Pool)
        {
            'client_name': 'Tanvi Chawla',
            'business_name': 'Chawla Fine Hospitality & Resorts',
            'location': 'Jaipur, Rajasthan',
            'contact_number': '+91 98777 66554',
            'whatsapp_number': '+91 98777 66554',
            'email': 'tanvi@chawlahotels.com',
            'business_category': 'Hospitality & Tourism',
            'lead_source': Lead.SOURCE_GOOGLE_ADS,
            'campaign_name': 'Google Ads Hospitality CRM Campaign',
            'lead_quality': Lead.QUALITY_WARM,
            'status': Lead.STATUS_NEW_LEAD, # REQUIREMENT 1
            'assigned_to': None, # Unassigned pool test
            'next_followup_date': today,
            'initial_notes': 'Captured via Google Search Ads. Wants lead management for wedding & event booking inquiries.',
            'followups': []
        },

        # Lead 8: Social Media Campaign - Cold / Unqualified Lead
        {
            'client_name': 'Karan Joshi',
            'business_name': 'Joshi Local Auto Repair',
            'location': 'Ahmedabad, Gujarat',
            'contact_number': '+91 98123 45678',
            'whatsapp_number': '+91 98123 45678',
            'email': 'karan.auto@gmail.com',
            'business_category': 'Automobile',
            'lead_source': Lead.SOURCE_SOCIAL_MEDIA,
            'campaign_name': 'Meta Facebook Broad Ads',
            'lead_quality': Lead.QUALITY_COLD,
            'status': Lead.STATUS_CONTACTED,
            'assigned_to': salespeople[0],
            'next_followup_date': next_week,
            'initial_notes': 'Solo mechanic shop; low software budget.',
            'followups': [
                ('Phone Call', timezone.now() - timedelta(days=1), 'Client indicated budget constraints under 5000/mo. Not a fit for enterprise plan right now.', 'Contacted', 'Cold', next_week)
            ]
        }
    ]

    for item in leads_data:
        followups = item.pop('followups', [])
        lead = Lead.objects.create(created_by=admin_user, **item)

        # Log creation activity
        ActivityLog.objects.create(
            lead=lead,
            user=admin_user,
            action=f"Lead Ingested ({lead.lead_source})",
            details=f"Recorded into database with initial status '{lead.status}'. Source: {lead.lead_source}."
        )

        for itype, idate, iremarks, istatus, iquality, inext in followups:
            FollowUp.objects.create(
                lead=lead,
                salesperson=lead.assigned_to or admin_user,
                interaction_type=itype,
                interaction_date=idate,
                remarks=iremarks,
                status_after_followup=istatus,
                quality_after_followup=iquality,
                next_followup_date=inext
            )

        print(f"  ✅ Created Lead: {lead.client_name} ({lead.business_name}) -> Status: {lead.status}")

    print("🎉 Database seeding completed successfully!")


if __name__ == '__main__':
    seed_database()

