from django.db import migrations, models


TESTIMONIALS = [
    {
        "quote": "RocketOps transformed our operations with their AI automation solutions. We've seen 40% increase in efficiency.",
        "author": "Ahmed Al-Mansouri",
        "title": "CEO, Tech Innovations UAE",
        "logo_id": "eurekad",
    },
    {
        "quote": "Outstanding service and expertise. Their team delivered beyond our expectations with custom ML models.",
        "author": "Sarah Johnson",
        "title": "Operations Director, Gulf Logistics",
        "logo_id": "nfdg",
    },
    {
        "quote": "Professional, reliable, and innovative. RocketOps is our go-to partner for all AI-related projects.",
        "author": "Omar Hassan",
        "title": "CTO, Digital Solutions Co.",
        "logo_id": "eureka",
    },
]

FAQS = [
    {
        "question": "What is RocketOps.ai and how does it help my business?",
        "answer": "RocketOps.ai is an AI-powered automation and integration platform designed to help startups and enterprises in the UAE and beyond eliminate manual tasks. It connects your tools, streamlines workflows, and enables scalable growth through intelligent automation — all without writing a single line of code.",
    },
    {
        "question": "Do I need technical or coding skills to use RocketOps.ai?",
        "answer": "No technical skills are required. RocketOps.ai offers a no-code workflow builder, ready-to-use templates, and guided setup. This allows business owners, marketers, and operations teams to create automations visually and deploy them instantly — even without IT support.",
    },
    {
        "question": "Can RocketOps integrate with my existing software and business tools?",
        "answer": "Yes. RocketOps integrates seamlessly with 1,000+ tools including CRMs, ERPs, Slack, Google Sheets, Notion, HubSpot, Airtable, and industry-specific systems. Custom integrations can also be built for local enterprise software commonly used across UAE and GCC businesses.",
    },
    {
        "question": "What type of AI automations can I create with RocketOps.ai?",
        "answer": "You can build voice and chat agents, automated email campaigns, data pipelines, and predictive analytics workflows. Our platform supports sales outreach bots, lead generation flows, report automation, and real-time monitoring — designed for business efficiency across Dubai, Abu Dhabi, and global markets.",
    },
    {
        "question": "Is customer support available after automation setup?",
        "answer": "Absolutely. Our Managed Automation Support team provides ongoing monitoring, optimization, and maintenance for all workflows. You’ll receive proactive updates, error-handling, and performance tuning to ensure continuous uptime and measurable business outcomes.",
    },
    {
        "question": "Can RocketOps.ai handle enterprise-level automation in the GCC region?",
        "answer": "Yes. RocketOps is built for scale — supporting multi-team operations, enterprise data security, and API-based automation infrastructure. Our GCC-based deployment options ensure data compliance, speed, and reliability for enterprises operating in regulated sectors.",
    },
    {
        "question": "Is RocketOps available in Arabic or other regional languages?",
        "answer": "Yes. RocketOps.ai supports Arabic language UI and localized documentation for GCC clients. Multi-language support helps regional teams collaborate efficiently without technical barriers.",
    },
]

CASE_STUDIES = [
    {
        "title": "RocketOps Ai empowers Pakways ERP to Automate complete workflows",
        "logo_text": "RocketOps Ai | Pakways ERP",
    },
    {
        "title": "RocketOps Ai empowers TravelWise to Enhance Customer Experience and automate their booking systems",
        "logo_text": "RocketOps Ai | TravelWise",
    },
    {
        "title": "RocketOps Ai enables TechDaddy to automate the client and freelauncers relations management",
        "logo_text": "RocketOps Ai | TechDaddy",
    },
    {
        "title": "RocketOps Ai helps Dosta to streamline operations and improve customer engagement and automate the deleiveries and orders system",
        "logo_text": "RocketOps Ai | Dosta",
    },
]


def seed(apps, schema_editor):
    Testimonial = apps.get_model('api', 'Testimonial')
    Faq = apps.get_model('api', 'Faq')
    CaseStudy = apps.get_model('api', 'CaseStudy')

    for i, t in enumerate(TESTIMONIALS):
        Testimonial.objects.get_or_create(
            author=t["author"],
            defaults={**t, "display_order": i, "is_active": True},
        )
    for i, f in enumerate(FAQS):
        Faq.objects.get_or_create(
            question=f["question"],
            defaults={**f, "display_order": i, "is_active": True},
        )
    for i, c in enumerate(CASE_STUDIES):
        CaseStudy.objects.get_or_create(
            title=c["title"],
            defaults={**c, "category": "Case Studies", "display_order": i, "is_active": True},
        )


def unseed(apps, schema_editor):
    apps.get_model('api', 'Testimonial').objects.all().delete()
    apps.get_model('api', 'Faq').objects.all().delete()
    apps.get_model('api', 'CaseStudy').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_aiprovider'),
    ]

    operations = [
        migrations.CreateModel(
            name='Testimonial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quote', models.TextField()),
                ('author', models.CharField(max_length=150)),
                ('title', models.CharField(help_text='Author title / company', max_length=200)),
                ('logo_id', models.CharField(blank=True, default='', max_length=50)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['display_order', 'id']},
        ),
        migrations.CreateModel(
            name='Faq',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=300)),
                ('answer', models.TextField()),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'verbose_name': 'FAQ', 'verbose_name_plural': 'FAQs', 'ordering': ['display_order', 'id']},
        ),
        migrations.CreateModel(
            name='CaseStudy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(default='Case Studies', max_length=100)),
                ('title', models.CharField(max_length=300)),
                ('logo_text', models.CharField(blank=True, default='', help_text='Text shown in the card logo area', max_length=200)),
                ('image', models.ImageField(blank=True, null=True, upload_to='case_studies/')),
                ('link', models.URLField(blank=True, default='')),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'verbose_name_plural': 'Case Studies', 'ordering': ['display_order', 'id']},
        ),
        migrations.RunPython(seed, unseed),
    ]
