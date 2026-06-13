from django.apps import AppConfig


class CrmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm'
    verbose_name = 'CRM'

    def ready(self):
        # Wire the website-contact → CRM lead ingestion signal.
        from . import signals  # noqa: F401
