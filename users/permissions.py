from rest_framework import permissions


class IsActiveEmployee(permissions.BasePermission):
    """
    Разрешение, проверяющее, является ли пользователь активным сотрудником.
    """

    def has_permission(self, request, view):
        # Проверяем, аутентифицирован ли пользователь
        if not request.user or not request.user.is_authenticated:
            return False

        # Проверяем, является ли пользователь активным сотрудником
        return request.user.is_active_employee