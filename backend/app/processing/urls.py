from django.urls import path
from .views import (
    SubmitTaskView, TaskStatusView, TaskResultView,
    WorkerChangeStatusView, WorkerSubmitResultView, WorkerNextTaskView,
    WorkerUploadURLView, TaskResultDownloadURLView, WorkerNextBatchView, WorkerHeartbeatView,
    AnalyzeDocumentView, AnalyzeWebsiteView, DetectDarkPatternsView, DetectSpecificPatternView,
)
urlpatterns = [
    path("tasks/submit/", SubmitTaskView.as_view(), name="task-submit"),
    path("tasks/<uuid:task_id>/status/", TaskStatusView.as_view(), name="task-status"),
    path("tasks/<uuid:task_id>/result/", TaskResultView.as_view(), name="task-result"),
    path("tasks/<uuid:task_id>/result/download_url/", TaskResultDownloadURLView.as_view(), name="task-result-download-url"),
    path("agents/analyze-document/", AnalyzeDocumentView.as_view(), name="analyze-document"),
    path("agents/analyze-website/", AnalyzeWebsiteView.as_view(), name="analyze-website"),
    path("agents/detect-dark-patterns/", DetectDarkPatternsView.as_view(), name="detect-dark-patterns"),
    path("agents/detect-pattern/", DetectSpecificPatternView.as_view(), name="detect-specific-pattern"),
    path("worker/tasks/next/", WorkerNextTaskView.as_view(), name="worker-task-next"),
    path("worker/tasks/next_batch/", WorkerNextBatchView.as_view(), name="worker-task-next-batch"),
    path("worker/tasks/<uuid:task_id>/status/", WorkerChangeStatusView.as_view(), name="worker-task-status"),
    path("worker/tasks/<uuid:task_id>/result/", WorkerSubmitResultView.as_view(), name="worker-task-result"),
    path("worker/tasks/<uuid:task_id>/upload_url/", WorkerUploadURLView.as_view(), name="worker-task-upload-url"),
    path("worker/tasks/<uuid:task_id>/heartbeat/", WorkerHeartbeatView.as_view(), name="worker-task-heartbeat"),
]
