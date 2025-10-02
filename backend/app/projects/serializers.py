from rest_framework import serializers
from .models import Project, Complaint
class ProjectPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "site_url", "status", "trust_score", "created_at"]
class ProjectOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "site_url", "status", "trust_score", "created_at", "updated_at"]
        read_only_fields = ["status", "trust_score", "created_at", "updated_at"]
class ProjectAdminRegSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"
class ComplaintSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    class Meta:
        model = Complaint
        fields = ["id", "project", "project_name", "complaint_type", "subject", "text",
                 "status", "response_text", "author", "author_name", "responded_by",
                 "created_at", "updated_at", "resolved_at"]
        read_only_fields = ["author", "created_at", "updated_at", "resolved_at"]
class ComplaintCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ["project", "complaint_type", "subject", "text"]
class ComplaintResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ["response_text", "status"]
