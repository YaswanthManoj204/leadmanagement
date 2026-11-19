from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Lead(models.Model):
    # Lead Sources
    SOURCE_SOCIAL_MEDIA = 'Social Media Paid Campaigns'
    SOURCE_GOOGLE_ADS = 'Google Ads'
    SOURCE_MANUAL = 'Manual Lead Entry'
    SOURCE_WEBSITE = 'Website Inbound'
    SOURCE_REFERRAL = 'Referral'
    SOURCE_OTHER = 'Other'

    SOURCE_CHOICES = (
        (SOURCE_SOCIAL_MEDIA, 'Social Media Paid Campaigns'),
        (SOURCE_GOOGLE_ADS, 'Google Ads'),
        (SOURCE_MANUAL, 'Manual Lead Entry'),
        (SOURCE_WEBSITE, 'Website Inbound'),
        (SOURCE_REFERRAL, 'Referral'),
        (SOURCE_OTHER, 'Other'),
    )

    # Lead Quality
    QUALITY_HOT = 'Hot'
    QUALITY_WARM = 'Warm'
    QUALITY_COLD = 'Cold'
    QUALITY_UNQUALIFIED = 'Unqualified'

    QUALITY_CHOICES = (
        (QUALITY_HOT, 'Hot (High Intent / Ready to Buy)'),
        (QUALITY_WARM, 'Warm (Interested / Exploring)'),
        (QUALITY_COLD, 'Cold (Low Activity / Unresponsive)'),
        (QUALITY_UNQUALIFIED, 'Unqualified (Not a Fit)'),
    )

    # Lead Statuses
    STATUS_NEW_LEAD = 'New Lead'
    STATUS_CONTACTED = 'Contacted'
    STATUS_IN_DISCUSSION = 'In Discussion'
    STATUS_QUALIFIED = 'Qualified'
    STATUS_PROPOSAL_SENT = 'Proposal Sent'
    STATUS_NEGOTIATION = 'Negotiation'
    STATUS_CLOSED_WON = 'Closed Won'
    STATUS_CLOSED_LOST = 'Closed Lost'

    STATUS_CHOICES = (
        (STATUS_NEW_LEAD, 'New Lead'),
        (STATUS_CONTACTED, 'Contacted'),
        (STATUS_IN_DISCUSSION, 'In Discussion'),
        (STATUS_QUALIFIED, 'Qualified'),
        (STATUS_PROPOSAL_SENT, 'Proposal Sent'),
        (STATUS_NEGOTIATION, 'Negotiation'),
        (STATUS_CLOSED_WON, 'Closed Won'),
        (STATUS_CLOSED_LOST, 'Closed Lost'),
    )

    # Business Categories
    CATEGORY_CHOICES = (
        ('Information Technology & Software', 'Information Technology & Software'),
        ('Real Estate & Construction', 'Real Estate & Construction'),
        ('Retail & E-commerce', 'Retail & E-commerce'),
        ('Healthcare & Pharmaceuticals', 'Healthcare & Pharmaceuticals'),
        ('Education & EdTech', 'Education & EdTech'),
        ('Finance & Banking', 'Finance & Banking'),
        ('Manufacturing & Industrial', 'Manufacturing & Industrial'),
        ('Hospitality & Tourism', 'Hospitality & Tourism'),
        ('Automobile', 'Automobile'),
        ('Professional & Legal Services', 'Professional & Legal Services'),
        ('Other', 'Other'),
    )

    # 1. Lead Information
    client_name = models.CharField(max_length=150, verbose_name="Client Name")
    business_name = models.CharField(max_length=200, verbose_name="Business Name")
    location = models.CharField(max_length=200, verbose_name="Location")
    contact_number = models.CharField(max_length=25, verbose_name="Contact Number")
    whatsapp_number = models.CharField(max_length=25, blank=True, null=True, verbose_name="WhatsApp Number")
    email = models.EmailField(blank=True, null=True, verbose_name="Email Address")
    business_category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Information Technology & Software')

    # 2. Lead Meta & Classification
    lead_source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    campaign_name = models.CharField(max_length=150, blank=True, null=True, help_text="Specific Ad Campaign name or UTM tag")
    lead_quality = models.CharField(max_length=20, choices=QUALITY_CHOICES, default=QUALITY_WARM)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_NEW_LEAD)

    # 3. Assignment & Follow-up Scheduling
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_leads', verbose_name="Salesperson Assigned"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_leads'
    )
    next_followup_date = models.DateField(blank=True, null=True, verbose_name="Next Follow-up Date")
    next_followup_time = models.TimeField(blank=True, null=True, verbose_name="Next Follow-up Time")
    initial_notes = models.TextField(blank=True, verbose_name="Initial Ingestion Notes / Inquiries")

    # 4. Closed Deal Details (Requirement 2 & 3: Complete business details when a deal is closed)
    deal_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Deal Value (₹/$)")
    closed_date = models.DateField(null=True, blank=True, verbose_name="Deal Closed Date")
    products_services_sold = models.TextField(blank=True, verbose_name="Products / Services Sold")
    contract_period = models.CharField(max_length=100, blank=True, verbose_name="Contract Period / Duration")
    payment_terms = models.CharField(max_length=100, blank=True, verbose_name="Payment Terms")
    billing_address = models.TextField(blank=True, verbose_name="Billing Address")
    tax_id = models.CharField(max_length=50, blank=True, verbose_name="Tax ID / GST / VAT")
    closure_notes = models.TextField(blank=True, verbose_name="Closure Remarks & Handover Notes")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client_name} - {self.business_name} ({self.status})"

    @property
    def assigned_name(self):
        if self.assigned_to:
            return self.assigned_to.get_full_name() or self.assigned_to.username
        return "Unassigned"

    @property
    def is_overdue(self):
        if self.next_followup_date and self.status not in [self.STATUS_CLOSED_WON, self.STATUS_CLOSED_LOST]:
            return self.next_followup_date < timezone.localdate()
        return False

    @property
    def is_due_today(self):
        if self.next_followup_date and self.status not in [self.STATUS_CLOSED_WON, self.STATUS_CLOSED_LOST]:
            return self.next_followup_date == timezone.localdate()
        return False

    @property
    def quality_badge_class(self):
        classes = {
            self.QUALITY_HOT: 'bg-danger text-white',
            self.QUALITY_WARM: 'bg-warning text-dark',
            self.QUALITY_COLD: 'bg-info text-dark',
            self.QUALITY_UNQUALIFIED: 'bg-secondary text-white',
        }
        return classes.get(self.lead_quality, 'bg-light text-dark')

    @property
    def status_badge_class(self):
        classes = {
            self.STATUS_NEW_LEAD: 'badge-new-lead',
            self.STATUS_CONTACTED: 'badge-contacted',
            self.STATUS_IN_DISCUSSION: 'badge-in-discussion',
            self.STATUS_QUALIFIED: 'badge-qualified',
            self.STATUS_PROPOSAL_SENT: 'badge-proposal',
            self.STATUS_NEGOTIATION: 'badge-negotiation',
            self.STATUS_CLOSED_WON: 'badge-closed-won',
            self.STATUS_CLOSED_LOST: 'badge-closed-lost',
        }
        return classes.get(self.status, 'bg-secondary')


class FollowUp(models.Model):
    INTERACTION_CHOICES = (
        ('Phone Call', 'Phone Call'),
        ('WhatsApp Message', 'WhatsApp Message'),
        ('Email', 'Email'),
        ('Online Meeting (Zoom/Meet)', 'Online Meeting (Zoom/Meet)'),
        ('In-person Meeting', 'In-person Meeting'),
        ('Product Demo', 'Product Demo'),
        ('Proposal Shared', 'Proposal Shared'),
        ('Internal Note', 'Internal Note'),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='followups')
    salesperson = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='followups_logged')
    interaction_type = models.CharField(max_length=50, choices=INTERACTION_CHOICES, default='Phone Call')
    interaction_date = models.DateTimeField(default=timezone.now)
    remarks = models.TextField(verbose_name="Discussion Remarks & Client Feedback")

    # Tracking updates made during follow-up
    status_after_followup = models.CharField(max_length=30, choices=Lead.STATUS_CHOICES)
    quality_after_followup = models.CharField(max_length=20, choices=Lead.QUALITY_CHOICES)
    next_followup_date = models.DateField(blank=True, null=True)
    next_followup_time = models.TimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-interaction_date']

    def __str__(self):
        return f"{self.interaction_type} with {self.lead.client_name} on {self.interaction_date.strftime('%Y-%m-%d')}"


class ActivityLog(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} on {self.lead.client_name} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
