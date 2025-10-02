from django.db import migrations, models
import django.db.models.deletion
import uuid
class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Worker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('token', models.CharField(max_length=255, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_seen', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('url', models.URLField()),
                ('status', models.CharField(choices=[('new','New'),('queued','Queued'),('in_progress','In Progress'),('done','Done'),('failed','Failed')], default='new', max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('error', models.TextField(blank=True, default="")),
                ('result_json', models.JSONField(blank=True, null=True)),
                ('result_s3_key', models.CharField(default="", blank=True, max_length=512)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='processing.worker')),
            ],
        ),
    ]
