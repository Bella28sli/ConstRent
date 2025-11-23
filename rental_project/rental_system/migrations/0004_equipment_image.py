from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rental_system', '0003_userpreference'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipment',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='equipment_images/'),
        ),
    ]
