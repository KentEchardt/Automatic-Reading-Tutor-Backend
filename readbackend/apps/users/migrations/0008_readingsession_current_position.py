# Generated by Django 5.0.7 on 2024-09-14 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_user_reading_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='readingsession',
            name='current_position',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
