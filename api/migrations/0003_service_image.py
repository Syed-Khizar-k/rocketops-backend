from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_service_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='services/',
                help_text='Display image shown on the /services listing page',
            ),
        ),
    ]
