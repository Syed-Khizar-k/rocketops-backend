from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='description',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Short description shown on the services list page and hero section'
            ),
        ),
    ]
