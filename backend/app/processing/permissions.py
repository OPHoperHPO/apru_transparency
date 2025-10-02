from rest_framework.permissions import BasePermission
from .models import Worker
class HasWorkerToken(BasePermission):
    message = "Worker token missing or invalid"
    def has_permission(self, request, view):
        token = request.headers.get("X-Worker-Token")
        if not token:
            return False
        try:
            worker = Worker.objects.get(token=token, is_active=True)
        except Worker.DoesNotExist:
            return False
        request.worker = worker
        return True
