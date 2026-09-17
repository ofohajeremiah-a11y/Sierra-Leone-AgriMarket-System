from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api', '0001_initial')]

    operations = [
        migrations.AlterField(
            model_name='alert', name='commodity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.commodity'),
        ),
        migrations.AlterField(
            model_name='alert', name='market',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.market'),
        ),
        migrations.AddField(model_name='alert', name='title', field=models.CharField(default='Market Alert', max_length=160)),
        migrations.AddField(model_name='alert', name='severity', field=models.CharField(choices=[('info','Information'),('warning','Warning'),('critical','Critical')], default='info', max_length=10)),
        migrations.AddField(model_name='alert', name='alert_type', field=models.CharField(choices=[('price_change','Price Change'),('price_submission','New Price'),('forecast_change','Forecast Change'),('opportunity','Market Opportunity'),('system','System')], default='system', max_length=30)),
        migrations.AddField(model_name='alert', name='previous_price', field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
        migrations.AddField(model_name='alert', name='current_price', field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
        migrations.AddField(model_name='alert', name='percent_change', field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
        migrations.AddField(model_name='alert', name='is_read', field=models.BooleanField(default=False)),
        migrations.AddIndex(model_name='alert', index=models.Index(fields=['user','is_read','created_at'], name='api_alert_user_id_2f4b9a_idx')),
    ]
