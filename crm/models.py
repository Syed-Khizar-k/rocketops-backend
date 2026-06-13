"""
RocketOps CRM — core data model.

The CRM sits inside the same Django project as the marketing/site API so that
everything (and, later, the AI Command Center) can read it directly. Website
contact submissions flow in automatically as leads (see ``signals.py``).

Entities:
    PipelineStage  — configurable kanban columns for deals
    Company        — an account / organisation
    Contact        — a person (lead → customer lifecycle)
    Deal           — an opportunity moving through the pipeline
    Activity       — timeline events + follow-up tasks
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


# ─────────────────────────────────────────────────────────────
#  Pipeline
# ─────────────────────────────────────────────────────────────
class PipelineStage(models.Model):
    """A column in the deal pipeline (e.g. New → Qualified → Proposal → Won)."""
    name = models.CharField(max_length=80, unique=True)
    order = models.PositiveIntegerField(default=0, help_text="Left-to-right order on the pipeline board.")
    probability = models.PositiveIntegerField(
        default=0,
        help_text="Default win probability (%) for deals in this stage.",
    )
    is_won = models.BooleanField(default=False, help_text="Deals reaching this stage are counted as won.")
    is_lost = models.BooleanField(default=False, help_text="Deals reaching this stage are counted as lost.")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Pipeline Stage"
        verbose_name_plural = "Pipeline Stages"

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────
#  Company (Account)
# ─────────────────────────────────────────────────────────────
class Company(models.Model):
    SIZE_CHOICES = [
        ('1-10', '1–10'),
        ('11-50', '11–50'),
        ('51-200', '51–200'),
        ('201-1000', '201–1000'),
        ('1000+', '1000+'),
    ]

    name = models.CharField(max_length=200)
    website = models.URLField(blank=True, default='')
    industry = models.CharField(max_length=120, blank=True, default='')
    size = models.CharField(max_length=20, blank=True, default='', choices=SIZE_CHOICES)
    country = models.CharField(max_length=100, blank=True, default='')
    phone = models.CharField(max_length=40, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='crm_companies',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────
#  Contact (Lead → Customer)
# ─────────────────────────────────────────────────────────────
class Contact(models.Model):
    LIFECYCLE_CHOICES = [
        ('lead', 'Lead'),
        ('mql', 'Marketing Qualified'),
        ('sql', 'Sales Qualified'),
        ('customer', 'Customer'),
        ('churned', 'Churned'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('working', 'Working'),
        ('qualified', 'Qualified'),
        ('unqualified', 'Unqualified'),
    ]
    SOURCE_CHOICES = [
        ('website', 'Website form'),
        ('referral', 'Referral'),
        ('manual', 'Manual entry'),
        ('import', 'Import'),
        ('other', 'Other'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField(blank=True, default='', db_index=True)
    phone = models.CharField(max_length=40, blank=True, default='')
    job_title = models.CharField(max_length=120, blank=True, default='')

    company = models.ForeignKey(
        Company, related_name='contacts', null=True, blank=True, on_delete=models.SET_NULL,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='crm_contacts',
        null=True, blank=True, on_delete=models.SET_NULL,
    )

    lifecycle_stage = models.CharField(max_length=12, choices=LIFECYCLE_CHOICES, default='lead')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='new')
    source = models.CharField(max_length=12, choices=SOURCE_CHOICES, default='manual')
    tags = models.CharField(max_length=255, blank=True, default='', help_text="Comma-separated tags.")

    # Link back to the originating website enquiry (if it came from the site form).
    source_submission = models.OneToOneField(
        'api.ContactSubmission', related_name='crm_contact',
        null=True, blank=True, on_delete=models.SET_NULL,
    )

    last_activity_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lifecycle_stage', '-created_at']),
            models.Index(fields=['status']),
        ]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def __str__(self):
        return self.full_name or self.email or f"Contact #{self.pk}"


# ─────────────────────────────────────────────────────────────
#  Deal (Opportunity)
# ─────────────────────────────────────────────────────────────
class Deal(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]

    name = models.CharField(max_length=200)
    company = models.ForeignKey(
        Company, related_name='deals', null=True, blank=True, on_delete=models.SET_NULL,
    )
    contact = models.ForeignKey(
        Contact, related_name='deals', null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Primary contact for this deal.",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='crm_deals',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    stage = models.ForeignKey(
        PipelineStage, related_name='deals', null=True, blank=True, on_delete=models.SET_NULL,
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='open')
    expected_close_date = models.DateField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    lost_reason = models.CharField(max_length=255, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        # Keep status / closed_at consistent with the stage's won/lost flags.
        if self.stage_id and self.stage:
            if self.stage.is_won:
                self.status = 'won'
            elif self.stage.is_lost:
                self.status = 'lost'
            else:
                self.status = 'open'
        if self.status in ('won', 'lost') and self.closed_at is None:
            self.closed_at = timezone.now()
        if self.status == 'open':
            self.closed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────
#  Activity (timeline + tasks)
# ─────────────────────────────────────────────────────────────
class Activity(models.Model):
    TYPE_CHOICES = [
        ('note', 'Note'),
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('task', 'Task'),
    ]

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='note')
    subject = models.CharField(max_length=255, blank=True, default='')
    body = models.TextField(blank=True, default='')

    contact = models.ForeignKey(
        Contact, related_name='activities', null=True, blank=True, on_delete=models.CASCADE,
    )
    deal = models.ForeignKey(
        Deal, related_name='activities', null=True, blank=True, on_delete=models.CASCADE,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='crm_activities',
        null=True, blank=True, on_delete=models.SET_NULL,
    )

    # Task-specific
    due_date = models.DateTimeField(null=True, blank=True, help_text="Set for follow-up tasks.")
    is_done = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Activities"
        indexes = [
            models.Index(fields=['type', 'is_done', 'due_date']),
        ]

    def save(self, *args, **kwargs):
        if self.is_done and self.completed_at is None:
            self.completed_at = timezone.now()
        if not self.is_done:
            self.completed_at = None
        super().save(*args, **kwargs)
        # Bump the related contact's last-activity stamp.
        if self.contact_id:
            Contact.objects.filter(pk=self.contact_id).update(last_activity_at=self.created_at or timezone.now())

    def __str__(self):
        return self.subject or self.get_type_display()
