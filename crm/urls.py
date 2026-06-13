from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PipelineStageViewSet, CompanyViewSet, ContactViewSet, DealViewSet, ActivityViewSet,
    DashboardView, login_view, logout_view, me_view, team_view,
)

router = DefaultRouter(trailing_slash=False)
router.register(r'stages', PipelineStageViewSet, basename='crm-stage')
router.register(r'companies', CompanyViewSet, basename='crm-company')
router.register(r'contacts', ContactViewSet, basename='crm-contact')
router.register(r'deals', DealViewSet, basename='crm-deal')
router.register(r'activities', ActivityViewSet, basename='crm-activity')

urlpatterns = [
    path('auth/login', login_view),
    path('auth/logout', logout_view),
    path('auth/me', me_view),
    path('team', team_view),
    path('dashboard', DashboardView.as_view()),
    path('', include(router.urls)),
]
