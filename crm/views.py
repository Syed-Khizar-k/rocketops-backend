from datetime import timedelta

from django.contrib.auth import authenticate
from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PipelineStage, Company, Contact, Deal, Activity
from .permissions import IsCRMUser, OwnerScopedQuerysetMixin, is_crm_admin, role_for
from .serializers import (
    PipelineStageSerializer, CompanySerializer,
    ContactListSerializer, ContactDetailSerializer,
    DealSerializer, ActivitySerializer, UserMiniSerializer,
)


# ─────────────────────────────────────────────────────────────
#  Auth
# ─────────────────────────────────────────────────────────────
def _user_payload(user):
    return {
        'id': user.id,
        'username': user.username,
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'role': role_for(user),
        'is_admin': is_crm_admin(user),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    user = authenticate(username=username, password=password)
    if user is None or not user.is_active:
        return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
    if not (user.is_staff or user.is_superuser or user.groups.exists()):
        return Response({'detail': 'This account has no CRM access.'}, status=status.HTTP_403_FORBIDDEN)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': _user_payload(user)})


@api_view(['POST'])
def logout_view(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def me_view(request):
    return Response(_user_payload(request.user))


# ─────────────────────────────────────────────────────────────
#  ViewSets
# ─────────────────────────────────────────────────────────────
class PipelineStageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PipelineStage.objects.all()
    serializer_class = PipelineStageSerializer
    permission_classes = [IsCRMUser]


class CompanyViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [IsCRMUser]

    def get_queryset(self):
        qs = Company.objects.select_related('owner').all()
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(industry__icontains=search))
        return self.scope_queryset(qs)

    def perform_create(self, serializer):
        serializer.save(owner=serializer.validated_data.get('owner') or self.request.user)


class ContactViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    permission_classes = [IsCRMUser]

    def get_serializer_class(self):
        return ContactListSerializer if self.action == 'list' else ContactDetailSerializer

    def get_queryset(self):
        qs = Contact.objects.select_related('company', 'owner').all()
        p = self.request.query_params
        if p.get('lifecycle'):
            qs = qs.filter(lifecycle_stage=p['lifecycle'])
        if p.get('status'):
            qs = qs.filter(status=p['status'])
        if p.get('source'):
            qs = qs.filter(source=p['source'])
        if p.get('owner'):
            qs = qs.filter(owner_id=p['owner'])
        if p.get('search'):
            s = p['search']
            qs = qs.filter(
                Q(first_name__icontains=s) | Q(last_name__icontains=s) |
                Q(email__icontains=s) | Q(company__name__icontains=s)
            )
        return self.scope_queryset(qs)

    def perform_create(self, serializer):
        serializer.save(owner=serializer.validated_data.get('owner') or self.request.user)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        contact = self.get_object()
        acts = contact.activities.select_related('owner').all()
        return Response(ActivitySerializer(acts, many=True).data)


class DealViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = DealSerializer
    permission_classes = [IsCRMUser]

    def get_queryset(self):
        qs = Deal.objects.select_related('company', 'contact', 'owner', 'stage').all()
        p = self.request.query_params
        if p.get('status'):
            qs = qs.filter(status=p['status'])
        if p.get('stage'):
            qs = qs.filter(stage_id=p['stage'])
        if p.get('owner'):
            qs = qs.filter(owner_id=p['owner'])
        if p.get('search'):
            qs = qs.filter(Q(name__icontains=p['search']) | Q(company__name__icontains=p['search']))
        return self.scope_queryset(qs)

    def perform_create(self, serializer):
        serializer.save(owner=serializer.validated_data.get('owner') or self.request.user)

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Move a deal to a different stage (used by the kanban board)."""
        deal = self.get_object()
        stage_id = request.data.get('stage')
        try:
            stage = PipelineStage.objects.get(pk=stage_id)
        except PipelineStage.DoesNotExist:
            return Response({'detail': 'Unknown stage.'}, status=status.HTTP_400_BAD_REQUEST)
        deal.stage = stage
        deal.save()
        return Response(DealSerializer(deal).data)


class ActivityViewSet(OwnerScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ActivitySerializer
    permission_classes = [IsCRMUser]

    def get_queryset(self):
        qs = Activity.objects.select_related('owner', 'contact', 'deal').all()
        p = self.request.query_params
        if p.get('contact'):
            qs = qs.filter(contact_id=p['contact'])
        if p.get('deal'):
            qs = qs.filter(deal_id=p['deal'])
        if p.get('type'):
            qs = qs.filter(type=p['type'])
        if p.get('tasks') == 'true':
            qs = qs.filter(type='task')
        if p.get('open') == 'true':
            qs = qs.filter(is_done=False)
        return self.scope_queryset(qs)

    def perform_create(self, serializer):
        serializer.save(owner=serializer.validated_data.get('owner') or self.request.user)


# ─────────────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────────────
class DashboardView(APIView):
    permission_classes = [IsCRMUser]

    def get(self, request):
        user = request.user
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        contacts = Contact.objects.all()
        deals = Deal.objects.all()
        activities = Activity.objects.all()
        if not is_crm_admin(user):
            contacts = contacts.filter(owner=user)
            deals = deals.filter(owner=user)
            activities = activities.filter(owner=user)

        open_deals = deals.filter(status='open')
        won_this_month = deals.filter(status='won', closed_at__gte=month_start)
        today = now.date()

        # Deals grouped by stage (for a mini funnel).
        by_stage = []
        for stage in PipelineStage.objects.all():
            sdeals = open_deals.filter(stage=stage)
            agg = sdeals.aggregate(c=Count('id'), v=Sum('amount'))
            by_stage.append({
                'stage': stage.name,
                'count': agg['c'] or 0,
                'value': float(agg['v'] or 0),
            })

        return Response({
            'new_leads_week': contacts.filter(created_at__gte=week_ago).count(),
            'total_contacts': contacts.count(),
            'open_deals': {
                'count': open_deals.count(),
                'value': float(open_deals.aggregate(v=Sum('amount'))['v'] or 0),
            },
            'won_this_month': {
                'count': won_this_month.count(),
                'value': float(won_this_month.aggregate(v=Sum('amount'))['v'] or 0),
            },
            'tasks_due_today': activities.filter(
                type='task', is_done=False, due_date__date__lte=today,
            ).count(),
            'deals_by_stage': by_stage,
            'recent_contacts': ContactListSerializer(
                contacts.select_related('company', 'owner')[:8], many=True,
            ).data,
            'upcoming_tasks': ActivitySerializer(
                activities.filter(type='task', is_done=False).order_by('due_date')[:6], many=True,
            ).data,
        })


@api_view(['GET'])
def team_view(request):
    """List CRM users (for owner assignment dropdowns) — admins only see the list."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.filter(is_active=True).filter(
        Q(is_staff=True) | Q(is_superuser=True) | Q(groups__isnull=False)
    ).distinct()
    return Response(UserMiniSerializer(users, many=True).data)
