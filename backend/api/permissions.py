from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Model
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.routers import APIRootView


class HasPermission(BasePermission):
    """
    Базовый класс разрешений с проверкой.
    """

    def has_permission(self, request, view: APIRootView):
        return bool(
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and request.user.is_active
        )


class AuthorStaffOrReadOnly(HasPermission):
    """
    Изменение только для администратора и автора.
    Остальным только чтение.
    """

    def has_object_permission(self, request, view: APIRootView, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and request.user.is_active
            and (
                request.user == obj.author
                or request.user.is_staff
            )
        )


class AdminOrReadOnly(HasPermission):
    """
    Создание и изменение только для администраторов.
    Остальным только чтение.
    """

    def has_object_permission(self, request: WSGIRequest, view: APIRootView):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and request.user.is_active
            and request.user.is_staff
        )


class OwnerUserOrReadOnly(HasPermission):
    """
    Создание и изменение только для администратора и пользователя.
    Остальным только чтение.
    """

    def has_object_permission(self, request, view: APIRootView, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and request.user.is_active
            and request.user == obj.author
            or request.user.is_staff
        )
