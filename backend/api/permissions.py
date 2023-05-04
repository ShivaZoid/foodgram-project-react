from rest_framework import permissions


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """
    Только автору или администратору позволено изменять объекты,
    а остальным только читать и просматривать.
    """

    def has_object_permission(self, request, view, obj):
        return (
            obj.author == request.user
            or request.method in permissions.SAFE_METHODS
            or request.user.is_superuser)


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Только администратору позволено изменять объекты,
    а остальным только читать и просматривать.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if user.is_authenticated and (user.is_superuser or user.is_staff):
            return True

        return False
