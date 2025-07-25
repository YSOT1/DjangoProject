# Generated by Django 5.1.4 on 2025-05-18 23:17

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medicalrecords', '0001_initial'),
        ('utilisateurs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DoctorRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(help_text='Rating from 1 to 5', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('comment', models.TextField(blank=True, help_text='Optional comment about the consultation')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='utilisateurs.doctor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='doctor_ratings', to='utilisateurs.patient')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('patient', 'doctor')},
            },
        ),
    ]
