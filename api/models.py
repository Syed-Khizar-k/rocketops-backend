from django.db import models

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
    description = models.TextField()
    image = models.ImageField(upload_to='products/')
    link = models.URLField()

    def __str__(self):
        return self.title

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
    link = models.URLField(blank=True, default='')
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
