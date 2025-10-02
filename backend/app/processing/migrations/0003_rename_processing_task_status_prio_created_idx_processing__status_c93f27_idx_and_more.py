import django.db.models.deletion
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('processing', '0002_queue_extras'),
        ('projects', '0002_safe_complaint_migration'),
    ]
    operations = [
        migrations.RenameIndex(
            model_name='task',
            new_name='processing__status_c93f27_idx',
            old_name='processing_task_status_prio_created_idx',
        ),
        migrations.RenameIndex(
            model_name='task',
            new_name='processing__status_f2bbde_idx',
            old_name='processing_task_status_assigned_idx',
        ),
        migrations.RenameIndex(
            model_name='task',
            new_name='processing__finishe_dc194b_idx',
            old_name='processing_task_finished_idx',
        ),
        migrations.RenameIndex(
            model_name='task',
            new_name='processing__status_539cee_idx',
            old_name='processing_task_status_hb_idx',
        ),
        migrations.AddField(
            model_name='task',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='projects.project'),
        ),
    ]
