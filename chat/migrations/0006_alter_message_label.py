# Generated by Django 4.2.3 on 2023-09-12 04:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_alter_message_label'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='label',
            field=models.TextField(blank=True, null=True),
        ),
    ]