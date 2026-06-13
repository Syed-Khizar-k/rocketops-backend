from django.contrib import admin
from django.utils.html import format_html

from .models import PipelineStage, Company, Contact, Deal, Activity


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'probability', 'is_won', 'is_lost')
    list_editable = ('order', 'probability', 'is_won', 'is_lost')
    ordering = ('order',)


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0
    fields = ('first_name', 'last_name', 'email', 'lifecycle_stage', 'status', 'owner')
    show_change_link = True


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'size', 'country', 'owner', 'created_at')
    list_filter = ('industry', 'size', 'country')
    search_fields = ('name', 'industry', 'website')
    inlines = [ContactInline]


class ActivityInline(admin.StackedInline):
    model = Activity
    extra = 0
    fk_name = 'contact'
    fields = ('type', 'subject', 'body', 'due_date', 'is_done', 'owner')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'company', 'lifecycle_badge', 'status', 'source', 'owner', 'created_at')
    list_filter = ('lifecycle_stage', 'status', 'source', 'owner')
    search_fields = ('first_name', 'last_name', 'email', 'company__name')
    autocomplete_fields = ('company',)
    inlines = [ActivityInline]
    readonly_fields = ('source_submission', 'last_activity_at', 'created_at', 'updated_at')

    @admin.display(description='Lifecycle')
    def lifecycle_badge(self, obj):
        colors = {'lead': '#5EE3FF', 'mql': '#FFB547', 'sql': '#BBDEF2', 'customer': '#3DD68C', 'churned': '#FF3B3B'}
        c = colors.get(obj.lifecycle_stage, '#8B95A4')
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>', c, obj.get_lifecycle_stage_display()
        )


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('name', 'stage', 'amount', 'currency', 'status', 'owner', 'expected_close_date')
    list_filter = ('status', 'stage', 'owner')
    search_fields = ('name', 'company__name', 'contact__first_name', 'contact__last_name')
    autocomplete_fields = ('company', 'contact')
    readonly_fields = ('closed_at', 'created_at', 'updated_at')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('subject', 'type', 'contact', 'deal', 'is_done', 'due_date', 'owner', 'created_at')
    list_filter = ('type', 'is_done', 'owner')
    search_fields = ('subject', 'body')
    autocomplete_fields = ('contact', 'deal')
