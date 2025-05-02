from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('websrv', '0003_cosponsor_img_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
                ('bill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='views', to='websrv.bill')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bill_views', to='websrv.user')),
            ],
            options={
                'ordering': ['-viewed_at'],
                'unique_together': {('user', 'bill')},
            },
        ),
    ] 