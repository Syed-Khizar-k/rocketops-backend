"""
Bootstrap the CRM: create the role groups and the default pipeline stages.

Idempotent — safe to run repeatedly.

    python manage.py seed_crm
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from crm.models import PipelineStage, Company, Contact, Deal, Activity
from crm.permissions import CRM_ADMIN_GROUP, SALES_REP_GROUP

DEFAULT_STAGES = [
    # name, order, probability, is_won, is_lost
    ('New', 1, 10, False, False),
    ('Qualified', 2, 30, False, False),
    ('Proposal', 3, 60, False, False),
    ('Negotiation', 4, 80, False, False),
    ('Won', 5, 100, True, False),
    ('Lost', 6, 0, False, True),
]


class Command(BaseCommand):
    help = "Create CRM role groups and default pipeline stages."

    def handle(self, *args, **options):
        # ── Pipeline stages ──────────────────────────────────────────
        for name, order, prob, won, lost in DEFAULT_STAGES:
            obj, created = PipelineStage.objects.get_or_create(
                name=name,
                defaults={'order': order, 'probability': prob, 'is_won': won, 'is_lost': lost},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  + stage: {name}"))

        # ── Role groups (with CRM model permissions) ─────────────────
        crm_models = [Company, Contact, Deal, Activity, PipelineStage]
        cts = [ContentType.objects.get_for_model(m) for m in crm_models]
        crm_perms = Permission.objects.filter(content_type__in=cts)

        admin_group, _ = Group.objects.get_or_create(name=CRM_ADMIN_GROUP)
        admin_group.permissions.set(crm_perms)
        self.stdout.write(self.style.SUCCESS(f"  + group: {CRM_ADMIN_GROUP} (full CRM perms)"))

        rep_group, _ = Group.objects.get_or_create(name=SALES_REP_GROUP)
        # Reps can view/add/change but not delete.
        rep_perms = crm_perms.exclude(codename__startswith='delete_')
        rep_group.permissions.set(rep_perms)
        self.stdout.write(self.style.SUCCESS(f"  + group: {SALES_REP_GROUP} (no delete)"))

        self.stdout.write(self.style.SUCCESS("CRM seed complete."))
