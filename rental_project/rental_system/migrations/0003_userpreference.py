from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rental_system', '0002_auto_20251122_1614'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('theme', models.CharField(choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System')], default='system', max_length=20)),
                ('date_format', models.CharField(choices=[('YYYY-MM-DD', 'YYYY-MM-DD'), ('DD.MM.YYYY', 'DD.MM.YYYY'), ('MM/DD/YYYY', 'MM/DD/YYYY')], default='DD.MM.YYYY', max_length=20)),
                ('number_format', models.CharField(choices=[('space', '1 234 567.89'), ('comma', '1,234,567.89'), ('dot', '1.234.567,89')], default='space', max_length=20)),
                ('page_size', models.PositiveIntegerField(default=50)),
                ('saved_filters', models.JSONField(blank=True, default=dict)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
