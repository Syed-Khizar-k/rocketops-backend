"""
Role model for the CRM.

Two groups drive visibility (managed via Django admin → Groups):
    "CRM Admin"  — full access to all records.
    "Sales Rep"  — sees only records they own.

Superusers always see everything. A user in neither group but authenticated is
treated as a Sales Rep (least privilege).
"""
from rest_framework.permissions import IsAuthenticated

CRM_ADMIN_GROUP = 'CRM Admin'
SALES_REP_GROUP = 'Sales Rep'


def is_crm_admin(user):
    return bool(
        user and user.is_authenticated and (
            user.is_superuser or user.groups.filter(name=CRM_ADMIN_GROUP).exists()
        )
    )


def role_for(user):
    if not (user and user.is_authenticated):
        return 'anonymous'
    if is_crm_admin(user):
        return 'admin'
    return 'rep'


class IsCRMUser(IsAuthenticated):
    """Any authenticated staff/CRM user may use the CRM API."""
    pass


class OwnerScopedQuerysetMixin:
    """
    Restrict a viewset's queryset to records owned by the requesting user unless
    they are a CRM admin. Set ``owner_field`` on the viewset (default ``owner``).
    """
    owner_field = 'owner'

    def scope_queryset(self, qs):
        user = self.request.user
        if is_crm_admin(user):
            return qs
        return qs.filter(**{self.owner_field: user})
