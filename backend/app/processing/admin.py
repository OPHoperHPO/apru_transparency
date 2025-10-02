from django.contrib import admin
from .models import Task, Worker
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "status", "priority", "project", "assigned_to", "created_at")
    search_fields = ("id", "url")
    list_filter = ("status", "priority")
@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "last_seen")
