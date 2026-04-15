from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField

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
    country = models.CharField(max_length=100)
    reach = models.CharField(max_length=100)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

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
