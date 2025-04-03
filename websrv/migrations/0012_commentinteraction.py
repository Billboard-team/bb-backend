# Generated by Django 4.2.3 on 2025-04-03 22:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('websrv', '0011_rename_password_comment_auth0_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auth0_id', models.CharField(max_length=255)),
                ('interaction_type', models.CharField(choices=[('like', 'Like'), ('dislike', 'Dislike')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='websrv.comment')),
            ],
            options={
                'unique_together': {('comment', 'auth0_id')},
            },
        ),
    ]
