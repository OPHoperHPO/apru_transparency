import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.RenameIndex(
            model_name='project',
            new_name='projects_pr_status_f023cb_idx',
            old_name='projects_pr_status_0b4d78_idx',
        ),
        migrations.RenameIndex(
            model_name='project',
            new_name='projects_pr_created_6b02e3_idx',
            old_name='projects_pr_created_1c7f4b_idx',
        ),
        migrations.DeleteModel(
            name='Complaint',
        ),
        migrations.CreateModel(
            name='Complaint',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('complaint_type', models.CharField(choices=[('false_positive', 'False Positive'), ('missing_pattern', 'Missing Pattern'), ('incorrect_severity', 'Incorrect Severity'), ('other', 'Other')], default='other', max_length=50)),
                ('subject', models.CharField(default='Complaint', max_length=200)),
                ('text', models.TextField()),
                ('status', models.CharField(choices=[('open', 'Open'), ('investigating', 'Investigating'), ('resolved', 'Resolved'), ('dismissed', 'Dismissed')], default='open', max_length=50)),
                ('response_text', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaints', to='projects.project')),
                ('responded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='complaint_responses', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
