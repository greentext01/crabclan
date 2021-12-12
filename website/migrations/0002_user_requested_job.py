# Generated by Django 3.2.8 on 2021-12-10 01:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='requested_job',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='requested', to='website.job'),
        ),
    ]