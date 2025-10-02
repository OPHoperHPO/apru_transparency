from django.db import models
import uuid
class Worker(models.Model):
    name = models.CharField(max_length=100, unique=True)
    token = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    def __str__(self): return self.name
class Task(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        QUEUED = "queued", "Queued"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField()
    project = models.ForeignKey('projects.Project', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.NEW)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.NORMAL)
    ttl_seconds = models.IntegerField(default=3600)
    max_retries = models.IntegerField(default=3)
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)
    progress = models.FloatField(null=True, blank=True)
    error = models.TextField(blank=True, default="")
    result_json = models.JSONField(null=True, blank=True)
    result_s3_key = models.CharField(max_length=512, blank=True, default="")
    class Meta:
        indexes = [
            models.Index(fields=["status", "priority", "created_at"]),
            models.Index(fields=["status", "assigned_to"]),
            models.Index(fields=["finished_at"]),
            models.Index(fields=["status", "heartbeat_at"]),
        ]
    def __str__(self):
        return f"Task {self.id} {self.status}"
