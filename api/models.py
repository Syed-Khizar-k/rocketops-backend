import re
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    linkedin_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='team/')

    def __str__(self):
        return self.name

class Service(models.Model):
    slug = models.SlugField(unique=True)
    header_label = models.CharField(max_length=100)
    header_title = models.CharField(max_length=200)
    description = models.TextField(
        blank=True,
        default='',
        help_text="Short description shown on the services list page and hero section"
    )
    image = models.ImageField(
        upload_to='services/',
        blank=True,
        null=True,
        help_text="Display image shown on the /services listing page"
    )

    def __str__(self):
        return self.header_title

class ServiceFeature(models.Model):
    service = models.ForeignKey(Service, related_name='features', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon_name = models.CharField(max_length=50, help_text="Icon identifier from frontend")

    def __str__(self):
        return f"{self.service.header_title} - {self.title}"

class Product(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=250)
    description = models.TextField()
    detailed_description = RichTextField(blank=True, null=True, help_text="Long description for the details page")

    image = models.ImageField(upload_to='products/', help_text="Main thumbnail image")
    link = models.URLField()
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'id']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='gallery', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.product.title} - Image {self.id}"

class ContactSubmission(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField()
    phone_country_code = models.CharField(max_length=8, blank=True, null=True)
    phone_number = models.CharField(max_length=32, blank=True, null=True)
    country = models.CharField(max_length=100)
    reach = models.CharField(max_length=100)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def full_phone(self):
        if self.phone_country_code and self.phone_number:
            return f"{self.phone_country_code} {self.phone_number}"
        return self.phone_number or ""

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"

class CompanyCategory(models.Model):
    name = models.CharField(max_length=100)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Company Categories"
        ordering = ['display_order']

    def __str__(self):
        return self.name

class CompanyLogo(models.Model):
    category = models.ForeignKey(CompanyCategory, related_name='logos', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='company_logos/')
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Testimonial(models.Model):
    quote = models.TextField()
    author = models.CharField(max_length=150)
    title = models.CharField(max_length=200, help_text="Author title / company")
    logo_id = models.CharField(max_length=50, blank=True, default='')
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'id']

    def __str__(self):
        return f"{self.author} — {self.title}"


class Faq(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class CaseStudy(models.Model):
    category = models.CharField(max_length=100, default='Case Studies')
    title = models.CharField(max_length=300)
    logo_text = models.CharField(max_length=200, blank=True, default='', help_text="Text shown in the card logo area")
    image = models.ImageField(upload_to='case_studies/', blank=True, null=True)
    product = models.ForeignKey(Product, related_name='case_studies', on_delete=models.SET_NULL, null=True, blank=True, help_text="Link this case study to a dynamic product page")
    link = models.URLField(blank=True, default='', help_text="External link (fallback if no product linked)")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name_plural = "Case Studies"

    def __str__(self):
        return self.title


class AIProvider(models.Model):
    name = models.CharField(max_length=100)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "AI Providers"
        ordering = ['display_order']

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
#  BLOG  (SEO-optimised content system)
# ─────────────────────────────────────────────
class BlogCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, blank=True, max_length=140)
    description = models.CharField(max_length=300, blank=True, default='')
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Blog(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    # ── Core ────────────────────────────────────────────────
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=220,
                            help_text="URL handle. Auto-generated from the title — change with care once published (affects SEO).")
    category = models.ForeignKey(
        BlogCategory, related_name='blogs', null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    excerpt = models.TextField(
        max_length=320,
        help_text="Short summary shown on blog cards and used as the fallback meta description.",
    )
    cover_image = models.ImageField(
        upload_to='blogs/covers/',
        help_text="Primary cover image. Recommended 1600×900 (16:9).",
    )
    cover_image_alt = models.CharField(
        max_length=200, blank=True, default='',
        help_text="Descriptive alt text for the cover image (SEO + accessibility).",
    )
    content = RichTextUploadingField(
        config_name='blog',
        help_text="Full article body. Supports headings, images, tables, lists, links and code.",
    )

    # ── Author ──────────────────────────────────────────────
    author_name = models.CharField(max_length=120, default='RocketOps Team')
    author_role = models.CharField(max_length=120, blank=True, default='')
    author_image = models.ImageField(upload_to='blogs/authors/', blank=True, null=True)

    read_time = models.PositiveIntegerField(
        default=0,
        help_text="Estimated read time in minutes. Auto-calculated from content when left at 0.",
    )

    # ── SEO ─────────────────────────────────────────────────
    meta_title = models.CharField(
        max_length=70, blank=True, default='',
        help_text="SEO page title tag (≤60 chars ideal). Falls back to the title.",
    )
    meta_description = models.CharField(
        max_length=200, blank=True, default='',
        help_text="SEO meta description (≤160 chars ideal). Falls back to the excerpt.",
    )
    focus_keyword = models.CharField(
        max_length=120, blank=True, default='',
        help_text="Primary keyword you want this article to rank for.",
    )
    keywords = models.TextField(
        blank=True, default='',
        help_text="Comma-separated SEO keywords / tags (e.g. fleet management, GCC, automation).",
    )
    canonical_url = models.URLField(
        blank=True, default='',
        help_text="Override the canonical URL. Leave blank to auto-generate from the slug.",
    )
    og_image = models.ImageField(
        upload_to='blogs/og/', blank=True, null=True,
        help_text="Social share image (1200×630). Falls back to the cover image.",
    )
    noindex = models.BooleanField(
        default=False,
        help_text="Tick to hide this article from search engines (noindex).",
    )

    # ── Publishing ──────────────────────────────────────────
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(
        default=False,
        help_text="Highlight this article at the top of the blog index.",
    )
    display_order = models.PositiveIntegerField(default=0)

    published_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Publish date — drives ordering and structured-data dates. Set automatically when first published.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_featured', 'display_order', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        # Auto read-time from word count (~200 wpm)
        if not self.read_time and self.content:
            words = len(re.sub(r'<[^>]+>', ' ', self.content).split())
            self.read_time = max(1, round(words / 200))
        # Stamp publish date on first publish
        if self.status == 'published' and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def keyword_list(self):
        return [k.strip() for k in self.keywords.split(',') if k.strip()]

    def __str__(self):
        return self.title


class BlogFAQ(models.Model):
    blog = models.ForeignKey(Blog, related_name='faqs', on_delete=models.CASCADE)
    question = models.CharField(max_length=300)
    answer = models.TextField(help_text="Plain text or simple HTML. Rendered in the FAQ schema for rich results.")
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Blog FAQ"
        verbose_name_plural = "Blog FAQs"
        ordering = ['display_order', 'id']

    def __str__(self):
        return self.question
