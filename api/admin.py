import csv
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from .models import TeamMember, Service, ServiceFeature, Product, ProductImage, ContactSubmission, CompanyCategory, CompanyLogo, AIProvider, Testimonial, Faq, CaseStudy

ICON_CHOICES = [
    ('IconGlobal',  'IconGlobal  — Globe / General'),
    ('IconStacks',  'IconStacks  — Stacked layers'),
    ('IconChart',   'IconChart   — Bar chart'),
    ('IconRefresh', 'IconRefresh — Refresh / Cycle'),
]

class ServiceFeatureForm(forms.ModelForm):
    icon_name = forms.ChoiceField(
        choices=ICON_CHOICES,
        widget=forms.Select(attrs={'style': 'width:260px'}),
        help_text='Choose which icon to display next to this feature on the website.',
    )

    class Meta:
        model = ServiceFeature
        fields = '__all__'


def export_as_csv(modeladmin, _request, queryset):
    """Generic CSV export action for any model."""
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{meta.verbose_name_plural}.csv"'
    writer = csv.writer(response)
    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    return response

export_as_csv.short_description = "⬇ Export selected to CSV"


# ─────────────────────────────────────────────
#  TEAM MEMBER
# ─────────────────────────────────────────────
@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('photo_thumb', 'name', 'category', 'linkedin_badge')
    list_display_links = ('name',)
    search_fields = ('name', 'category')
    ordering = ('id',)
    list_per_page = 20
    actions = [export_as_csv]

    def photo_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;border-radius:50%;'
                'object-fit:cover;border:2px solid #3a3a3a;" />',
                obj.image.url,
            )
        return format_html('<span style="color:#555;font-size:11px;">No photo</span>')
    photo_thumb.short_description = ''

    def linkedin_badge(self, obj):
        if obj.linkedin_url:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer" '
                'style="display:inline-flex;align-items:center;gap:5px;'
                'background:#0a66c2;color:#fff;padding:3px 10px;'
                'border-radius:20px;font-size:11px;font-weight:600;'
                'text-decoration:none;">in LinkedIn</a>',
                obj.linkedin_url,
            )
        return format_html('<span style="color:#555;font-size:11px;">—</span>')
    linkedin_badge.short_description = 'LinkedIn'


# ─────────────────────────────────────────────
#  SERVICE + FEATURE INLINE
# ─────────────────────────────────────────────
class ServiceFeatureInline(admin.TabularInline):
    model = ServiceFeature
    form = ServiceFeatureForm
    extra = 1
    fields = ('title', 'description', 'icon_name')
    show_change_link = True


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('image_thumb', 'header_title', 'slug', 'feature_count', 'frontend_link')
    list_display_links = ('header_title',)
    prepopulated_fields = {'slug': ('header_title',)}
    inlines = [ServiceFeatureInline]
    search_fields = ('header_title', 'slug', 'description')
    ordering = ('id',)
    list_per_page = 20
    readonly_fields = ('image_preview',)
    fields = ('header_title', 'slug', 'header_label', 'description', 'image', 'image_preview')

    def image_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:64px;height:44px;border-radius:8px;'
                'object-fit:cover;border:1px solid #3a3a3a;" />',
                obj.image.url,
            )
        return format_html(
            '<span style="display:inline-block;width:64px;height:44px;'
            'background:#1a1a1a;border:1px dashed #333;border-radius:8px;'
            'line-height:44px;text-align:center;color:#555;font-size:10px;">'
            'No img</span>'
        )
    image_thumb.short_description = ''

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:340px;max-height:220px;'
                'border-radius:10px;border:1px solid #2a2a2a;margin-top:6px;" />',
                obj.image.url,
            )
        return format_html('<span style="color:#555;font-size:12px;">No image uploaded yet.</span>')
    image_preview.short_description = 'Image preview'

    def feature_count(self, obj):
        count = obj.features.count()
        color = '#7b68ee' if count >= 4 else '#f59e0b' if count >= 1 else '#ef4444'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:20px;font-size:11px;font-weight:600;">'
            '{} feature{}</span>',
            color, count, 's' if count != 1 else '',
        )
    feature_count.short_description = 'Features'

    def frontend_link(self, obj):
        return format_html(
            '<a href="/services/{}" target="_blank" '
            'style="color:#7b68ee;font-size:12px;text-decoration:none;">'
            '↗ View page</a>',
            obj.slug,
        )
    frontend_link.short_description = 'Frontend'


# ─────────────────────────────────────────────
#  PRODUCT + GALLERY INLINE
# ─────────────────────────────────────────────
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'display_order')
    show_change_link = True

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('image_thumb', 'title', 'slug', 'description_preview', 'visit_link')
    list_display_links = ('title',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductImageInline]
    search_fields = ('title', 'slug', 'description')
    ordering = ('id',)
    list_per_page = 20
    actions = [export_as_csv]

    def image_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:64px;height:44px;border-radius:8px;'
                'object-fit:cover;border:1px solid #3a3a3a;" />',
                obj.image.url,
            )
        return format_html('<span style="color:#555;font-size:11px;">No image</span>')
    image_thumb.short_description = ''

    def description_preview(self, obj):
        text = obj.description
        return text[:90] + '…' if len(text) > 90 else text
    description_preview.short_description = 'Description'

    def visit_link(self, obj):
        if obj.link:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer" '
                'style="color:#7b68ee;font-size:12px;text-decoration:none;">'
                '↗ Visit</a>',
                obj.link,
            )
        return format_html('<span style="color:#555;">—</span>')
    visit_link.short_description = 'Link'


# ─────────────────────────────────────────────
#  CONTACT SUBMISSION
# ─────────────────────────────────────────────
REACH_COLORS = {
    'Careers':       '#10b981',
    'Partnerships':  '#3b82f6',
    'Press':         '#f59e0b',
    'Support':       '#ef4444',
    'Other':         '#8b5cf6',
}


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'email_display', 'company',
        'reach_badge', 'country', 'submitted_at',
    )
    list_display_links = ('full_name',)
    readonly_fields = ('created_at',)
    list_filter = ('reach', 'country', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'company', 'details')
    ordering = ('-created_at',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = [export_as_csv]

    def full_name(self, obj):
        return format_html(
            '<strong style="color:#e0e0e0;">{} {}</strong>',
            obj.first_name, obj.last_name,
        )
    full_name.short_description = 'Name'
    full_name.admin_order_field = 'first_name'

    def email_display(self, obj):
        return format_html(
            '<a href="mailto:{}" style="color:#7b68ee;text-decoration:none;">{}</a>',
            obj.email, obj.email,
        )
    email_display.short_description = 'Email'
    email_display.admin_order_field = 'email'

    def reach_badge(self, obj):
        color = REACH_COLORS.get(obj.reach, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:20px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.reach,
        )
    reach_badge.short_description = 'Reach'
    reach_badge.admin_order_field = 'reach'

    def submitted_at(self, obj):
        return format_html(
            '<span style="color:#888;font-size:12px;">{}</span>',
            obj.created_at.strftime('%b %d, %Y  %H:%M'),
        )
    submitted_at.short_description = 'Submitted'
    submitted_at.admin_order_field = 'created_at'


# ─────────────────────────────────────────────
#  COMPANY LOGOS
# ─────────────────────────────────────────────
class CompanyLogoInline(admin.TabularInline):
    model = CompanyLogo
    extra = 1
    fields = ('name', 'image', 'alt_text', 'display_order')
    classes = ('collapse',)


@admin.register(CompanyCategory)
class CompanyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'logo_count')
    list_editable = ('display_order',)
    inlines = [CompanyLogoInline]
    ordering = ('display_order',)
    search_fields = ('name',)

    def logo_count(self, obj):
        count = obj.logos.count()
        return format_html(
            '<span style="background:#4f46e5;color:#fff;padding:2px 10px;'
            'border-radius:20px;font-size:11px;font-weight:600;">'
            '{} logos</span>',
            count,
        )
    logo_count.short_description = 'Logos'


@admin.register(CompanyLogo)
class CompanyLogoAdmin(admin.ModelAdmin):
    list_display = ('image_thumb', 'name', 'category', 'display_order')
    list_display_links = ('name',)
    list_editable = ('display_order',)
    list_filter = ('category',)
    search_fields = ('name', 'category__name')
    ordering = ('category', 'display_order')

    def image_thumb(self, obj):
        if obj.image:
            return format_html(
                '<div style="background:#0a0a0a; padding:6px; border-radius:6px; display:inline-block; border:1px solid #333;">'
                '<img src="{}" style="height:30px; width:auto; max-width:120px; object-fit:contain;" />'
                '</div>',
                obj.image.url,
            )
        return format_html('<span style="color:#555;font-size:11px;">No logo</span>')
    image_thumb.short_description = 'Preview'


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order')
    list_editable = ('display_order',)
    ordering = ('display_order',)
    search_fields = ('name',)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('author', 'title', 'quote_preview', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('author', 'title', 'quote')
    ordering = ('display_order', 'id')

    def quote_preview(self, obj):
        return (obj.quote[:80] + '…') if len(obj.quote) > 80 else obj.quote
    quote_preview.short_description = 'Quote'


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ('question', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('question', 'answer')
    ordering = ('display_order', 'id')


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'product', 'logo_text', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    list_filter = ('is_active', 'category', 'product')
    search_fields = ('title', 'logo_text', 'category')
    ordering = ('display_order', 'id')
