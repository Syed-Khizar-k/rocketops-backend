from django.db.models import F
from rest_framework import viewsets, mixins
from .models import (
    TeamMember, Service, Product, ContactSubmission, CompanyCategory, AIProvider,
    Testimonial, Faq, CaseStudy, BlogCategory, Blog,
)
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
    BlogCategorySerializer,
    BlogListSerializer,
    BlogDetailSerializer,
)

class TeamMemberViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeamMember.objects.all().order_by('id')
    serializer_class = TeamMemberSerializer

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all().order_by('id')
    serializer_class = ServiceSerializer
    lookup_field = 'slug'

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all().order_by('display_order', 'id')
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


class BlogCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    lookup_field = 'slug'


class BlogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public blog API.

    list:     GET /api/blogs/                 (lightweight cards)
              GET /api/blogs/?category=<slug>
              GET /api/blogs/?featured=true
              GET /api/blogs/?search=<term>
    retrieve: GET /api/blogs/<slug>/          (full article + FAQs + related)
    """
    lookup_field = 'slug'

    def get_queryset(self):
        qs = (
            Blog.objects.filter(status='published')
            .select_related('category')
            .prefetch_related('faqs')
        )
        if self.action == 'list':
            params = self.request.query_params
            category = params.get('category')
            if category:
                qs = qs.filter(category__slug=category)
            if params.get('featured') in ('true', '1'):
                qs = qs.filter(is_featured=True)
            search = params.get('search')
            if search:
                from django.db.models import Q
                qs = qs.filter(
                    Q(title__icontains=search)
                    | Q(excerpt__icontains=search)
                    | Q(keywords__icontains=search)
                )
        return qs

    def get_serializer_class(self):
        return BlogListSerializer if self.action == 'list' else BlogDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        # Non-blocking view counter (avoids updated_at churn via F-expression).
        Blog.objects.filter(slug=kwargs.get('slug')).update(views=F('views') + 1)
        return response
