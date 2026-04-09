from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeamMemberViewSet, ServiceViewSet, ProductViewSet, ContactSubmissionViewSet,
    CompanyCategoryViewSet, AIProviderViewSet,
    TestimonialViewSet, FaqViewSet, CaseStudyViewSet,
)

router = DefaultRouter()
router.register(r'teams', TeamMemberViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'products', ProductViewSet)
router.register(r'contact', ContactSubmissionViewSet)
router.register(r'companies', CompanyCategoryViewSet)
router.register(r'aiproviders', AIProviderViewSet)
router.register(r'testimonials', TestimonialViewSet)
router.register(r'faqs', FaqViewSet)
router.register(r'case-studies', CaseStudyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
