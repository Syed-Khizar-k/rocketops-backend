from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import PipelineStage, Company, Contact, Deal, Activity

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'email']

    def get_name(self, obj):
        full = obj.get_full_name()
        return full or obj.username


class PipelineStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineStage
        fields = ['id', 'name', 'order', 'probability', 'is_won', 'is_lost']


class CompanySerializer(serializers.ModelSerializer):
    owner_detail = UserMiniSerializer(source='owner', read_only=True)
    contact_count = serializers.IntegerField(source='contacts.count', read_only=True)

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'website', 'industry', 'size', 'country', 'phone',
            'notes', 'owner', 'owner_detail', 'contact_count', 'created_at', 'updated_at',
        ]


class ContactListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True, default='')
    owner_detail = UserMiniSerializer(source='owner', read_only=True)

    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'job_title', 'company', 'company_name', 'owner', 'owner_detail',
            'lifecycle_stage', 'status', 'source', 'tags',
            'last_activity_at', 'created_at',
        ]


class ContactDetailSerializer(ContactListSerializer):
    tag_list = serializers.ListField(read_only=True)
    deal_count = serializers.IntegerField(source='deals.count', read_only=True)

    class Meta(ContactListSerializer.Meta):
        fields = ContactListSerializer.Meta.fields + [
            'tag_list', 'deal_count', 'source_submission', 'updated_at',
        ]


class DealSerializer(serializers.ModelSerializer):
    owner_detail = UserMiniSerializer(source='owner', read_only=True)
    stage_detail = PipelineStageSerializer(source='stage', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True, default='')
    contact_name = serializers.CharField(source='contact.full_name', read_only=True, default='')

    class Meta:
        model = Deal
        fields = [
            'id', 'name', 'company', 'company_name', 'contact', 'contact_name',
            'owner', 'owner_detail', 'stage', 'stage_detail',
            'amount', 'currency', 'status', 'expected_close_date', 'closed_at',
            'lost_reason', 'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'closed_at']


class ActivitySerializer(serializers.ModelSerializer):
    owner_detail = UserMiniSerializer(source='owner', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True, default='')

    class Meta:
        model = Activity
        fields = [
            'id', 'type', 'subject', 'body', 'contact', 'contact_name', 'deal',
            'owner', 'owner_detail', 'due_date', 'is_done', 'completed_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['completed_at']
