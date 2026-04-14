from rest_framework import viewsets, mixins
from .models import TeamMember, Service, Product, ContactSubmission, CompanyCategory, AIProvider, Testimonial, Faq, CaseStudy
from .serializers import (
    TeamMemberSerializer,
    ServiceSerializer,
    ProductSerializer,
    ContactSubmissionSerializer,
    CompanyCategorySerializer,
    AIProviderSerializer,
    TestimonialSerializer,
    FaqSerializer,
    CaseStudySerializer,
)

class TeamMemberViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeamMember.objects.all().order_by('id')
    serializer_class = TeamMemberSerializer

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all().order_by('id')
    serializer_class = ServiceSerializer
    lookup_field = 'slug'

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all().order_by('id')
    serializer_class = ProductSerializer
    lookup_field = 'slug'

class ContactSubmissionViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = ContactSubmission.objects.all()
    serializer_class = ContactSubmissionSerializer

class CompanyCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CompanyCategory.objects.all().prefetch_related('logos')
    serializer_class = CompanyCategorySerializer

class AIProviderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIProvider.objects.all()
    serializer_class = AIProviderSerializer


class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Testimonial.objects.filter(is_active=True)
    serializer_class = TestimonialSerializer


class FaqViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Faq.objects.filter(is_active=True)
    serializer_class = FaqSerializer


class CaseStudyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CaseStudy.objects.filter(is_active=True)
    serializer_class = CaseStudySerializer
