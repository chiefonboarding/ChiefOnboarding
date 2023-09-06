from django.contrib.auth import get_user_model
from rest_framework import permissions


class AdminPermission(permissions.BasePermission):
    """
    Global permission check for administrator.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == get_user_model().Role.ADMIN
        )
