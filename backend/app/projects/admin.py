from django.contrib import admin
from .models import Project, Complaint
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "site_url", "status", "trust_score")
    search_fields = ("name", "site_url", "id")
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("project", "author", "created_at")
