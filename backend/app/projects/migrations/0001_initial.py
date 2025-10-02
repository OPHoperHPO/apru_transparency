from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings
class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('site_url', models.URLField()),
                ('status', models.CharField(choices=[('draft','Draft'),('submitted','Submitted'),('under_review','Under Review'),('approved','Approved'),('rejected','Rejected')], default='draft', max_length=32)),
                ('trust_score', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Complaint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaints', to='projects.project')),
            ],
        ),
        migrations.AddIndex(model_name='project', index=models.Index(fields=['status'], name='projects_pr_status_0b4d78_idx')),
        migrations.AddIndex(model_name='project', index=models.Index(fields=['created_at'], name='projects_pr_created_1c7f4b_idx')),
    ]
