from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [('processing', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='task',
            name='priority',
            field=models.CharField(choices=[('low','Low'),('normal','Normal'),('high','High')], default='normal', max_length=16),
        ),
        migrations.AddField(model_name='task', name='ttl_seconds', field=models.IntegerField(default=3600)),
        migrations.AddField(model_name='task', name='max_retries', field=models.IntegerField(default=3)),
        migrations.AddField(model_name='task', name='retry_count', field=models.IntegerField(default=0)),
        migrations.AddField(model_name='task', name='heartbeat_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='task', name='progress', field=models.FloatField(blank=True, null=True)),
        migrations.AddIndex(model_name='task', index=models.Index(fields=['status','priority','created_at'], name='processing_task_status_prio_created_idx')),
        migrations.AddIndex(model_name='task', index=models.Index(fields=['status','assigned_to'], name='processing_task_status_assigned_idx')),
        migrations.AddIndex(model_name='task', index=models.Index(fields=['finished_at'], name='processing_task_finished_idx')),
        migrations.AddIndex(model_name='task', index=models.Index(fields=['status','heartbeat_at'], name='processing_task_status_hb_idx')),
    ]
