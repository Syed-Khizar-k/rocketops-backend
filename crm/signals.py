"""
Lead ingestion: every website contact-form submission becomes a CRM lead.

When a visitor submits the marketing site's contact form (``api.ContactSubmission``)
we create a matching CRM ``Contact`` (source = website), open a ``Deal`` in the first
pipeline stage, and log the enquiry as a note on the timeline. Idempotent — a
submission already linked to a contact is skipped.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from api.models import ContactSubmission
from .models import Contact, Deal, Activity, PipelineStage


@receiver(post_save, sender=ContactSubmission, dispatch_uid="crm_ingest_contact_submission")
def ingest_contact_submission(sender, instance, created, **kwargs):
    if not created:
        return
    # Idempotency guard (also protects re-runs / fixtures).
    if Contact.objects.filter(source_submission=instance).exists():
        return

    phone = instance.full_phone if hasattr(instance, 'full_phone') else ''

    contact = Contact.objects.create(
        first_name=instance.first_name or 'Unknown',
        last_name=instance.last_name or '',
        email=instance.email or '',
        phone=phone,
        job_title=instance.job_title or '',
        lifecycle_stage='lead',
        status='new',
        source='website',
        source_submission=instance,
        tags=instance.reach or '',
    )

    # Open a deal in the first (non-won/lost) stage so it lands on the board.
    first_stage = (
        PipelineStage.objects.filter(is_won=False, is_lost=False).order_by('order', 'id').first()
        or PipelineStage.objects.order_by('order', 'id').first()
    )
    company_label = instance.company or contact.full_name or 'New enquiry'
    interest = instance.reach or 'enquiry'
    Deal.objects.create(
        name=f"{company_label} — {interest}",
        contact=contact,
        stage=first_stage,
        status='open',
    )

    # Log the original message as the first timeline entry.
    detail_lines = []
    if instance.company:
        detail_lines.append(f"Company: {instance.company}")
    if instance.country:
        detail_lines.append(f"Country: {instance.country}")
    if instance.reach:
        detail_lines.append(f"Interested in: {instance.reach}")
    if instance.details:
        detail_lines.append("")
        detail_lines.append(instance.details)

    Activity.objects.create(
        type='note',
        subject='Website enquiry received',
        body="\n".join(detail_lines).strip(),
        contact=contact,
    )
