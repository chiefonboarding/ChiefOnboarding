from rest_framework import permissions


class AdminPermission(permissions.BasePermission):
    """
    Global permission check for administrator.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 1


class ManagerPermission(permissions.BasePermission):
    """
    Global permission check for a manager.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 1 or request.user.role == 2)


class NewHirePermission(permissions.BasePermission):
    """
    Global permission check for employer.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated
