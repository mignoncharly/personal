from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import User


def is_admin_user(user) -> bool:
    return bool(
        user and user.is_authenticated
        and (user.is_superuser or getattr(user, "role", None) == User.Role.ADMIN)
    )


class IsAdmin(BasePermission):
    """Nur Admins (Rolle admin oder Superuser)."""

    message = "Diese Aktion ist Administratoren vorbehalten."

    def has_permission(self, request, view):
        return is_admin_user(request.user)


class IsAdminOrReadOnly(BasePermission):
    """Lesen für alle Angemeldeten, Schreiben nur für Admins."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return is_admin_user(request.user)


class IsSelfOrAdmin(BasePermission):
    """Objektzugriff nur auf eigene Daten – Admins sehen alles."""

    def has_object_permission(self, request, view, obj):
        if is_admin_user(request.user):
            return True
        owner = getattr(obj, "employee_id", None) or getattr(obj, "user_id", None) or getattr(obj, "id", None)
        return owner == request.user.id
