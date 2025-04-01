# Generated by Django 4.2.3 on 2025-04-01 17:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('websrv', '0007_aisummary'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cosponsor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bioguide_id', models.CharField(max_length=20, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('middle_name', models.CharField(blank=True, max_length=100, null=True)),
                ('last_name', models.CharField(max_length=100)),
                ('full_name', models.CharField(max_length=255)),
                ('party', models.CharField(max_length=10)),
                ('state', models.CharField(max_length=5)),
                ('district', models.IntegerField(blank=True, null=True)),
                ('is_original_cosponsor', models.BooleanField()),
                ('sponsorship_date', models.DateField()),
                ('url', models.URLField()),
            ],
        ),
        migrations.AddField(
            model_name='bill',
            name='cosponsors',
            field=models.ManyToManyField(related_name='bills', to='websrv.cosponsor'),
        ),
    ]
