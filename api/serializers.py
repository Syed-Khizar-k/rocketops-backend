from rest_framework import serializers
from .models import TeamMember, Service, ServiceFeature, Product, ContactSubmission, CompanyCategory, CompanyLogo, AIProvider, Testimonial, Faq, CaseStudy


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


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'image', 'link']

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

    class Meta:
        model = CaseStudy
        fields = ['id', 'category', 'title', 'logo_text', 'image', 'link', 'display_order']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
