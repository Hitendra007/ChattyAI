# Generated by Django 4.2.3 on 2023-09-12 05:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_alter_message_label'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='label',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]