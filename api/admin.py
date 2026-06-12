import csv
from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.http import HttpResponse
from .models import (
    TeamMember, Service, ServiceFeature, Product, ProductImage, ContactSubmission,
    CompanyCategory, CompanyLogo, AIProvider, Testimonial, Faq, CaseStudy,
    BlogCategory, Blog, BlogFAQ,
)

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
            '<a href="{}/services/{}" target="_blank" rel="noopener" '
            'style="color:#7b68ee;font-size:12px;text-decoration:none;">'
            '↗ View page</a>',
            settings.SITE_URL, obj.slug,
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
    list_display = ('image_thumb', 'title', 'slug', 'description_preview', 'display_order', 'visit_link')
    list_display_links = ('title',)
    list_editable = ('display_order',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductImageInline]
    search_fields = ('title', 'slug', 'description')
    ordering = ('display_order', 'id')
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
        'full_name', 'email_display', 'phone_display', 'company',
        'reach_badge', 'country', 'submitted_at',
    )
    list_display_links = ('full_name',)
    list_filter = ('reach', 'country', 'created_at')
    search_fields = (
        'first_name', 'last_name', 'email',
        'phone_number', 'company', 'details',
    )
    ordering = ('-created_at',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = [export_as_csv]

    # Detail view shows a single read-only "card" instead of editable inputs.
    readonly_fields = ('submission_card',)
    fields = ('submission_card',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    # ── list-view helpers ──────────────────────────────────────
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

    def phone_display(self, obj):
        phone = obj.full_phone
        if not phone:
            return format_html('<span style="color:#555;font-size:12px;">—</span>')
        tel = ''.join(ch for ch in phone if ch.isdigit() or ch == '+')
        return format_html(
            '<a href="tel:{}" style="color:#7b68ee;text-decoration:none;'
            'font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;">{}</a>',
            tel, phone,
        )
    phone_display.short_description = 'Phone'

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

    # ── detail-view card ───────────────────────────────────────
    def submission_card(self, obj):
        if obj is None or obj.pk is None:
            return format_html('<em style="color:#666;">Submission not saved yet.</em>')

        reach_color = REACH_COLORS.get(obj.reach, '#6b7280')
        phone = obj.full_phone or '—'
        phone_tel = ''.join(ch for ch in phone if ch.isdigit() or ch == '+') if phone != '—' else ''
        phone_html = (
            format_html(
                '<a href="tel:{}" style="color:#e0e0e0;text-decoration:none;">{}</a>',
                phone_tel, phone,
            )
            if phone_tel else
            format_html('<span style="color:#666;">—</span>')
        )

        def row(label, value_html):
            return format_html(
                '<tr>'
                '<td style="padding:10px 14px;color:#888;font-size:12px;'
                'text-transform:uppercase;letter-spacing:0.5px;width:160px;'
                'border-bottom:1px solid #1f1f1f;vertical-align:top;">{}</td>'
                '<td style="padding:10px 14px;color:#e0e0e0;font-size:14px;'
                'border-bottom:1px solid #1f1f1f;">{}</td>'
                '</tr>',
                label, value_html,
            )

        rows = format_html(
            '{}{}{}{}{}{}{}{}{}',
            row('Name', format_html(
                '<strong>{} {}</strong>', obj.first_name, obj.last_name,
            )),
            row('Email', format_html(
                '<a href="mailto:{}" style="color:#7b68ee;'
                'text-decoration:none;">{}</a>',
                obj.email, obj.email,
            )),
            row('Phone', phone_html),
            row('Company', format_html(
                '{}', obj.company or format_html('<span style="color:#666;">—</span>'),
            )),
            row('Job title', format_html(
                '{}', obj.job_title or format_html('<span style="color:#666;">—</span>'),
            )),
            row('Country', format_html('{}', obj.country)),
            row('Reach', format_html(
                '<span style="background:{};color:#fff;padding:3px 12px;'
                'border-radius:20px;font-size:11px;font-weight:600;">{}</span>',
                reach_color, obj.reach,
            )),
            row('Submitted', format_html(
                '<span style="color:#aaa;">{}</span>',
                obj.created_at.strftime('%B %d, %Y · %H:%M'),
            )),
            row('Message', format_html(
                '<div style="background:#0f0f0f;border:1px solid #222;'
                'border-radius:8px;padding:14px 16px;color:#dcdcdc;'
                'line-height:1.55;white-space:pre-wrap;font-size:14px;'
                'max-width:640px;">{}</div>',
                obj.details,
            )),
        )

        return format_html(
            '<div style="background:#161616;border:1px solid #262626;'
            'border-radius:12px;padding:8px;max-width:820px;'
            'box-shadow:0 1px 0 rgba(255,255,255,0.02);">'
            '<table style="width:100%;border-collapse:collapse;">'
            '{}'
            '</table>'
            '</div>',
            rows,
        )
    submission_card.short_description = 'Submission details'


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


# ─────────────────────────────────────────────
#  BLOG
# ─────────────────────────────────────────────
@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order', 'post_count')
    list_editable = ('display_order',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    ordering = ('display_order', 'name')

    def post_count(self, obj):
        count = obj.blogs.count()
        return format_html(
            '<span style="background:#4f46e5;color:#fff;padding:2px 10px;'
            'border-radius:20px;font-size:11px;font-weight:600;">{} post{}</span>',
            count, '' if count == 1 else 's',
        )
    post_count.short_description = 'Posts'


class BlogFAQInline(admin.StackedInline):
    """Per-blog FAQs. Add as many as needed — each blog manages its own set,
    rendered at the end of the article + emitted as FAQPage schema for rich results."""
    model = BlogFAQ
    extra = 1
    fields = ('question', 'answer', 'display_order')
    verbose_name = "FAQ for this article"
    verbose_name_plural = "FAQs for this article  ·  add as many as you need (shown at the end of the post + Google FAQ rich snippet)"


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = (
        'cover_thumb', 'title', 'category', 'status_badge',
        'featured_badge', 'read_time_badge', 'seo_health', 'published_at', 'frontend_link',
    )
    list_display_links = ('title',)
    list_filter = ('status', 'is_featured', 'category', 'created_at')
    search_fields = ('title', 'excerpt', 'keywords', 'focus_keyword', 'meta_title')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-is_featured', 'display_order', '-published_at')
    list_per_page = 20
    date_hierarchy = 'published_at'
    inlines = [BlogFAQInline]
    actions = [export_as_csv, 'make_published', 'make_draft', 'mark_featured']
    readonly_fields = ('cover_preview', 'og_preview', 'created_at', 'updated_at', 'views', 'seo_health')

    fieldsets = (
        ('Article', {
            'fields': ('title', 'slug', 'category', 'excerpt', 'content'),
        }),
        ('Cover image', {
            'fields': ('cover_image', 'cover_image_alt', 'cover_preview'),
        }),
        ('Author', {
            'classes': ('collapse',),
            'fields': ('author_name', 'author_role', 'author_image', 'read_time'),
        }),
        ('SEO & structured data', {
            'description': 'Drives the page title tag, meta description, Open Graph, Twitter cards, '
                           'canonical URL, keywords and JSON-LD schema on the frontend.',
            'fields': (
                'seo_health',
                'meta_title', 'meta_description',
                'focus_keyword', 'keywords',
                'canonical_url', 'og_image', 'og_preview', 'noindex',
            ),
        }),
        ('Publishing', {
            'fields': ('status', 'is_featured', 'display_order', 'published_at',
                       ('created_at', 'updated_at', 'views')),
        }),
    )

    # ── list helpers ────────────────────────────────────────
    def cover_thumb(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width:72px;height:46px;border-radius:8px;'
                'object-fit:cover;border:1px solid #3a3a3a;" />',
                obj.cover_image.url,
            )
        return format_html('<span style="color:#555;font-size:11px;">No cover</span>')
    cover_thumb.short_description = ''

    def status_badge(self, obj):
        color = '#10b981' if obj.status == 'published' else '#6b7280'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase;">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def featured_badge(self, obj):
        if obj.is_featured:
            return format_html(
                '<span style="background:#f59e0b;color:#1a1a1a;padding:2px 9px;'
                'border-radius:20px;font-size:11px;font-weight:700;">★ Featured</span>'
            )
        return format_html('<span style="color:#555;">—</span>')
    featured_badge.short_description = 'Featured'

    def read_time_badge(self, obj):
        return format_html(
            '<span style="color:#8b95a4;font-size:12px;">{} min</span>', obj.read_time or '—',
        )
    read_time_badge.short_description = 'Read'

    def seo_health(self, obj):
        """Quick at-a-glance SEO checklist."""
        checks = [
            ('Meta title', bool(obj.meta_title) or bool(obj.title)),
            ('Meta description', bool(obj.meta_description) or bool(obj.excerpt)),
            ('Focus keyword', bool(obj.focus_keyword)),
            ('Keywords', bool(obj.keywords)),
            ('Cover alt text', bool(obj.cover_image_alt)),
            ('FAQs', obj.pk is not None and obj.faqs.exists()),
        ]
        passed = sum(1 for _, ok in checks if ok)
        total = len(checks)
        ratio = passed / total
        color = '#10b981' if ratio >= 0.83 else '#f59e0b' if ratio >= 0.5 else '#ef4444'
        rows = format_html_join(
            '',
            '<div style="display:flex;align-items:center;gap:6px;font-size:12px;'
            'color:#cbd5e1;margin:2px 0;"><span style="color:{};">{}</span> {}</div>',
            ((('#10b981' if ok else '#ef4444'), ('✓' if ok else '✕'), label) for label, ok in checks),
        )
        return format_html(
            '<div style="line-height:1.4;">'
            '<div style="font-weight:700;color:{};margin-bottom:4px;">SEO {}/{}</div>{}'
            '</div>',
            color, passed, total, rows,
        )
    seo_health.short_description = 'SEO health'

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width:420px;max-height:240px;border-radius:10px;'
                'border:1px solid #2a2a2a;margin-top:6px;" />', obj.cover_image.url,
            )
        return format_html('<span style="color:#555;font-size:12px;">No cover uploaded yet.</span>')
    cover_preview.short_description = 'Cover preview'

    def og_preview(self, obj):
        img = obj.og_image or obj.cover_image
        if img:
            return format_html(
                '<img src="{}" style="max-width:360px;max-height:189px;border-radius:8px;'
                'border:1px solid #2a2a2a;margin-top:6px;" /><div style="color:#666;'
                'font-size:11px;margin-top:4px;">Social share preview (falls back to cover)</div>',
                img.url,
            )
        return format_html('<span style="color:#555;font-size:12px;">No social image.</span>')
    og_preview.short_description = 'OG preview'

    def frontend_link(self, obj):
        if obj.status != 'published':
            return format_html(
                '<span style="color:#6b7280;font-size:12px;" title="Publish the article to view it on the site.">draft · not live</span>'
            )
        return format_html(
            '<a href="{}/blogs/{}" target="_blank" rel="noopener" '
            'style="color:#7b68ee;font-size:12px;text-decoration:none;">↗ View</a>',
            settings.SITE_URL, obj.slug,
        )
    frontend_link.short_description = 'Frontend'

    # ── actions ─────────────────────────────────────────────
    @admin.action(description="✅ Publish selected articles")
    def make_published(self, request, queryset):
        from django.utils import timezone
        for blog in queryset:
            if blog.published_at is None:
                blog.published_at = timezone.now()
            blog.status = 'published'
            blog.save()
        self.message_user(request, f"{queryset.count()} article(s) published.")

    @admin.action(description="📝 Move selected to draft")
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f"{updated} article(s) moved to draft.")

    @admin.action(description="★ Mark selected as featured")
    def mark_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} article(s) marked as featured.")
