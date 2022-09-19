from rest_framework import permissions


class IsOwnerorReadonly(permissions.BasePermission):
    def has_object_permission(self, request, view, event):
        if request.user in permissions.SAFE_METHODS:
            return True
        if request.user == event.event_owner:
            return True
        return False
