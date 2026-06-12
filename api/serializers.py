from rest_framework import serializers
from .models import (
    TeamMember, Service, ServiceFeature, Product, ProductImage, ContactSubmission,
    CompanyCategory, CompanyLogo, AIProvider, Testimonial, Faq, CaseStudy,
    BlogCategory, Blog, BlogFAQ,
)


class TeamMemberSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = ['id', 'name', 'category', 'linkedin_url', 'image']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ServiceFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFeature
        fields = ['id', 'title', 'description', 'icon_name']


class ServiceSerializer(serializers.ModelSerializer):
    features = ServiceFeatureSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ['id', 'slug', 'header_label', 'header_title', 'description', 'image', 'features']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'display_order']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    gallery = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'description', 'detailed_description', 'image', 'gallery', 'link', 'display_order']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ContactSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = '__all__'
        read_only_fields = ('created_at',)

class CompanyLogoSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = CompanyLogo
        fields = ['id', 'name', 'image', 'alt_text', 'display_order']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class CompanyCategorySerializer(serializers.ModelSerializer):
    logos = CompanyLogoSerializer(many=True, read_only=True)

    class Meta:
        model = CompanyCategory
        fields = ['id', 'name', 'display_order', 'logos']

class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = ['id', 'name', 'display_order']


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ['id', 'quote', 'author', 'title', 'logo_id', 'display_order']


class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faq
        fields = ['id', 'question', 'answer', 'display_order']


class CaseStudySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    product_slug = serializers.CharField(source='product.slug', read_only=True)

    class Meta:
        model = CaseStudy
        fields = ['id', 'category', 'title', 'logo_text', 'image', 'product_slug', 'link', 'display_order']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


# ─────────────────────────────────────────────
#  BLOG
# ─────────────────────────────────────────────
class _AbsoluteImageMixin:
    """Shared helper to build absolute media URLs."""
    def _abs(self, image):
        if not image:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(image.url) if request else image.url


class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = ['id', 'name', 'slug', 'description', 'display_order']


class BlogFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogFAQ
        fields = ['id', 'question', 'answer', 'display_order']


class BlogListSerializer(_AbsoluteImageMixin, serializers.ModelSerializer):
    """Lightweight payload for the /blogs index — no heavy body content."""
    cover_image = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.name', read_only=True, default=None)
    category_slug = serializers.CharField(source='category.slug', read_only=True, default=None)
    keywords = serializers.ListField(source='keyword_list', read_only=True)

    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'excerpt', 'cover_image', 'cover_image_alt',
            'category', 'category_slug', 'author_name', 'author_role',
            'read_time', 'is_featured', 'keywords', 'published_at',
        ]

    def get_cover_image(self, obj):
        return self._abs(obj.cover_image)


class BlogDetailSerializer(_AbsoluteImageMixin, serializers.ModelSerializer):
    """Full payload for /blogs/<slug> — body, FAQs, SEO + related posts."""
    cover_image = serializers.SerializerMethodField()
    og_image = serializers.SerializerMethodField()
    author_image = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.name', read_only=True, default=None)
    category_slug = serializers.CharField(source='category.slug', read_only=True, default=None)
    keywords = serializers.ListField(source='keyword_list', read_only=True)
    faqs = BlogFAQSerializer(many=True, read_only=True)
    related = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'excerpt', 'content',
            'cover_image', 'cover_image_alt', 'og_image',
            'category', 'category_slug',
            'author_name', 'author_role', 'author_image',
            'read_time', 'views',
            'meta_title', 'meta_description', 'focus_keyword', 'keywords',
            'canonical_url', 'noindex',
            'is_featured', 'published_at', 'updated_at',
            'faqs', 'related',
        ]

    def get_cover_image(self, obj):
        return self._abs(obj.cover_image)

    def get_og_image(self, obj):
        return self._abs(obj.og_image) or self._abs(obj.cover_image)

    def get_author_image(self, obj):
        return self._abs(obj.author_image)

    def get_related(self, obj):
        qs = Blog.objects.filter(status='published').exclude(pk=obj.pk)
        if obj.category_id:
            qs = qs.filter(category_id=obj.category_id)
        related = list(qs[:3])
        if len(related) < 3:
            extra = Blog.objects.filter(status='published').exclude(
                pk__in=[obj.pk, *[b.pk for b in related]]
            )[: 3 - len(related)]
            related += list(extra)
        return BlogListSerializer(related, many=True, context=self.context).data
