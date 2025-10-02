from django.utils import timezone
from django.db import transaction, models
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Task
from .serializers import (
    TaskSubmitSerializer, TaskStatusSerializer, TaskResultSerializer,
    WorkerStatusUpdateSerializer, WorkerResultSerializer
)
from .permissions import HasWorkerToken
from app.common.s3 import presign_put, presign_get
from app.projects.models import Project
class SubmitTaskView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = TaskSubmitSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        task = Task.objects.create(url=s.validated_data["url"], status=Task.Status.NEW)
        return Response({"id": str(task.id)}, status=status.HTTP_201_CREATED)
class TaskStatusView(RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = TaskStatusSerializer
    lookup_url_kwarg = "task_id"
    queryset = Task.objects.all()
    lookup_field = "id"
class TaskResultView(RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = TaskResultSerializer
    lookup_url_kwarg = "task_id"
    queryset = Task.objects.all()
    lookup_field = "id"
class WorkerChangeStatusView(APIView):
    permission_classes = [HasWorkerToken]
    def patch(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        s = WorkerStatusUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        new_status = s.validated_data["status"]
        task.status = new_status
        if new_status == Task.Status.IN_PROGRESS:
            task.assigned_to = request.worker
            task.started_at = timezone.now()
            task.heartbeat_at = task.started_at
        if new_status in (Task.Status.DONE, Task.Status.FAILED):
            task.finished_at = timezone.now()
        if "error" in s.validated_data:
            task.error = s.validated_data["error"]
        task.save(update_fields=["status","assigned_to","started_at","finished_at","heartbeat_at","error","updated_at"])
        return Response({"ok": True})
class WorkerSubmitResultView(APIView):
    permission_classes = [HasWorkerToken]
    def post(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        s = WorkerResultSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        payload = s.validated_data
        if "result_json" in payload:
            task.result_json = payload["result_json"]
        if "result_s3_key" in payload:
            task.result_s3_key = payload["result_s3_key"]
        task.status = Task.Status.DONE
        task.finished_at = timezone.now()
        task.assigned_to = getattr(request, "worker", None)
        task.save(update_fields=["result_json","result_s3_key","status","finished_at","assigned_to","updated_at"])
        return Response({"ok": True})
class WorkerNextTaskView(APIView):
    permission_classes = [HasWorkerToken]
    def post(self, request):
        with transaction.atomic():
            task = (
                Task.objects.select_for_update(skip_locked=True)
                .filter(status__in=[Task.Status.NEW, Task.Status.QUEUED])
                .order_by(models.Case(
                    models.When(priority=Task.Priority.HIGH, then=0),
                    models.When(priority=Task.Priority.NORMAL, then=1),
                    models.When(priority=Task.Priority.LOW, then=2),
                    default=3,
                    output_field=models.IntegerField(),
                ), "created_at")
                .first()
            )
            if not task:
                return Response({"task": None})
            now = timezone.now()
            task.status = Task.Status.IN_PROGRESS
            task.assigned_to = request.worker
            task.started_at = now
            task.heartbeat_at = now
            task.save(update_fields=["status","assigned_to","started_at","heartbeat_at","updated_at"])
        return Response({"id": str(task.id), "url": task.url, "priority": task.priority, "ttl_seconds": task.ttl_seconds})
class WorkerNextBatchView(APIView):
    permission_classes = [HasWorkerToken]
    def post(self, request):
        limit = int(request.data.get('limit', 5))
        taken = []
        now = timezone.now()
        with transaction.atomic():
            qs = (
                Task.objects.select_for_update(skip_locked=True)
                .filter(status__in=[Task.Status.NEW, Task.Status.QUEUED])
                .order_by(models.Case(
                    models.When(priority=Task.Priority.HIGH, then=0),
                    models.When(priority=Task.Priority.NORMAL, then=1),
                    models.When(priority=Task.Priority.LOW, then=2),
                    default=3,
                    output_field=models.IntegerField(),
                ), "created_at")
            )
            for task in qs[:limit]:
                task.status = Task.Status.IN_PROGRESS
                task.assigned_to = request.worker
                task.started_at = now
                task.heartbeat_at = now
                task.save(update_fields=["status","assigned_to","started_at","heartbeat_at","updated_at"])
                taken.append({"id": str(task.id), "url": task.url, "priority": task.priority, "ttl_seconds": task.ttl_seconds})
        return Response({"tasks": taken})
class WorkerHeartbeatView(APIView):
    permission_classes = [HasWorkerToken]
    def patch(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        if task.assigned_to_id != getattr(request, 'worker', None).id:
            return Response({"detail": "Forbidden"}, status=403)
        task.heartbeat_at = timezone.now()
        progress = request.data.get('progress')
        if progress is not None:
            try: task.progress = float(progress)
            except ValueError: pass
        task.save(update_fields=["heartbeat_at","progress","updated_at"])
        return Response({"ok": True})
class WorkerUploadURLView(APIView):
    permission_classes = [HasWorkerToken]
    def post(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        filename = request.data.get('filename', 'result.bin')
        content_type = request.data.get('content_type')
        key = f"tasks/{task.id}/{filename}"
        url = presign_put(key, content_type=content_type, expires=3600)
        return Response({"key": key, "url": url, "method": "PUT"}, status=200)
class TaskResultDownloadURLView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        if not task.result_s3_key:
            return Response({"detail": "No S3 result"}, status=404)
        url = presign_get(task.result_s3_key, expires=600)
        return Response({"url": url, "expires_in": 600}, status=200)
class AnalyzeDocumentView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        from .tasks import analyze_document_with_legal_llm
        document_file = request.FILES.get('file')
        project_id = request.data.get('project_id')
        if not document_file:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        from app.agents.document_extractor import validate_file_type
        if not validate_file_type(document_file.name):
            return Response(
                {"detail": f"Unsupported file type. Supported types: PDF, Word (.doc/.docx), TXT"},
                status=status.HTTP_400_BAD_REQUEST
            )
        project = None
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                pass
        task = Task.objects.create(
            url=f"document:{document_file.name}",
            project=project,
            status=Task.Status.QUEUED
        )
        file_content = document_file.read()
        analyze_document_with_legal_llm.delay(str(task.id), file_content, document_file.name)
        return Response({
            "id": str(task.id),
            "status": "queued"
        }, status=status.HTTP_201_CREATED)
class AnalyzeWebsiteView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        from .tasks import analyze_website_with_browser_agent
        url = request.data.get('url')
        project_id = request.data.get('project_id')
        if not url:
            return Response({"detail": "URL is required"}, status=status.HTTP_400_BAD_REQUEST)
        project = None
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                pass
        task = Task.objects.create(
            url=url,
            project=project,
            status=Task.Status.QUEUED
        )
        analyze_website_with_browser_agent.delay(str(task.id), url)
        return Response({
            "id": str(task.id),
            "status": "queued"
        }, status=status.HTTP_201_CREATED)
class DetectDarkPatternsView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        from .tasks import detect_all_dark_patterns
        url = request.data.get('url')
        project_id = request.data.get('project_id')
        if not url:
            return Response({"detail": "URL is required"}, status=status.HTTP_400_BAD_REQUEST)
        project = None
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                pass
        task = Task.objects.create(
            url=url,
            project=project,
            status=Task.Status.QUEUED
        )
        detect_all_dark_patterns.delay(str(task.id), url)
        return Response({
            "id": str(task.id),
            "status": "queued",
            "message": "Dark pattern detection initiated for 12 patterns"
        }, status=status.HTTP_201_CREATED)
class DetectSpecificPatternView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        url = request.data.get('url')
        pattern_type = request.data.get('pattern_type')
        project_id = request.data.get('project_id')
        if not url:
            return Response({"detail": "URL is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not pattern_type:
            return Response({"detail": "pattern_type is required"}, status=status.HTTP_400_BAD_REQUEST)
        pattern_task_map = {
            'roach_motel': 'detect_roach_motel_pattern',
            'fake_urgency': 'detect_fake_urgency_pattern',
            'drip_pricing': 'detect_drip_pricing_pattern',
        }
        if pattern_type not in pattern_task_map:
            return Response({
                "detail": f"Unknown pattern type. Available: {', '.join(pattern_task_map.keys())}"
            }, status=status.HTTP_400_BAD_REQUEST)
        project = None
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                pass
        task = Task.objects.create(
            url=url,
            project=project,
            status=Task.Status.QUEUED
        )
        from .tasks import (
            detect_roach_motel_pattern,
            detect_fake_urgency_pattern,
            detect_drip_pricing_pattern
        )
        task_function = {
            'roach_motel': detect_roach_motel_pattern,
            'fake_urgency': detect_fake_urgency_pattern,
            'drip_pricing': detect_drip_pricing_pattern,
        }[pattern_type]
        task_function.delay(str(task.id), url)
        return Response({
            "id": str(task.id),
            "status": "queued",
            "pattern_type": pattern_type
        }, status=status.HTTP_201_CREATED)
