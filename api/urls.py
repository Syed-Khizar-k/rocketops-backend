from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeamMemberViewSet, ServiceViewSet, ProductViewSet, ContactSubmissionViewSet

router = DefaultRouter()
router.register(r'teams', TeamMemberViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'products', ProductViewSet)
router.register(r'contact', ContactSubmissionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
