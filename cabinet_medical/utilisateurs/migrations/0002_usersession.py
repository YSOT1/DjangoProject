# Generated by Django 5.1.4 on 2025-05-20 00:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utilisateurs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(max_length=40, unique=True)),
                ('ip_address', models.GenericIPAddressField(null=True)),
                ('user_agent', models.TextField(null=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='utilisateurs.utilisateurs')),
            ],
            options={
                'ordering': ['-last_activity'],
            },
        ),
    ]
