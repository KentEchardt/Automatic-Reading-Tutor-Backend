from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsTeacher(permissions.BasePermission):
    """
    Allows access only to teacher users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'


class IsReader(permissions.BasePermission):
    """
    Allows access only to reader users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'reader'
