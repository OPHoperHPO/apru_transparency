from rest_framework import serializers
from .models import Task
class TaskSubmitSerializer(serializers.Serializer):
    url = serializers.URLField()
class TaskIdSerializer(serializers.Serializer):
    id = serializers.UUIDField()
class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "status", "created_at", "updated_at", "error"]
class TaskResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "result_json", "result_s3_key", "finished_at"]
class WorkerStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Task.Status.choices)
    error = serializers.CharField(required=False, allow_blank=True)
class WorkerResultSerializer(serializers.Serializer):
    result_json = serializers.JSONField(required=False)
    result_s3_key = serializers.CharField(required=False, allow_blank=True)
