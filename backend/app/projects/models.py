from django.db import models
from django.conf import settings
import uuid
class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=255)
    site_url = models.URLField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    trust_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
    def __str__(self):
        return f"{self.name} ({self.id})"
class Complaint(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        INVESTIGATING = "investigating", "Investigating"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"
    class Type(models.TextChoices):
        FALSE_POSITIVE = "false_positive", "False Positive"
        MISSING_PATTERN = "missing_pattern", "Missing Pattern"
        INCORRECT_SEVERITY = "incorrect_severity", "Incorrect Severity"
        OTHER = "other", "Other"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="complaints")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    complaint_type = models.CharField(max_length=50, choices=Type.choices, default=Type.OTHER)
    subject = models.CharField(max_length=200, default="Complaint")
    text = models.TextField()
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.OPEN)
    response_text = models.TextField(blank=True, null=True)
    responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="complaint_responses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"Complaint #{self.id} - {self.subject}"
