# Generated by Django 5.0.7 on 2024-08-29 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_story_id_alter_story_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
