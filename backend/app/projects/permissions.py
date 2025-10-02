from rest_framework.permissions import BasePermission, SAFE_METHODS
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'))
class IsRegulator(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', '') == 'regulator')
class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', '') == 'owner' and obj.owner_id == request.user.id)
class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
                return True
            return getattr(request.user, 'role', '') == 'owner' and obj.owner_id == request.user.id
        return False
class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
