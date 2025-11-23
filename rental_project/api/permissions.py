from rest_framework import permissions


def _in_groups(user, group_names):
    return user.is_authenticated and user.groups.filter(name__in=group_names).exists()


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return bool(request.user and request.user.is_staff)


class AdminOrGroupsWrite(permissions.BasePermission):
    """
    Чтение — всем аутентифицированным. Запись — только is_staff или участникам указанных групп.
    Leader/прочие группы будут иметь только чтение, если не входят в groups.
    """

    groups = []

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or _in_groups(request.user, self.groups))
        )


class AdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class AdminOrManagersWrite(AdminOrGroupsWrite):
    groups = ["Менеджер"]


class AdminOrTechniciansWrite(AdminOrGroupsWrite):
    groups = ["Техник"]


class AdminOnlyWrite(AdminOrGroupsWrite):
    groups = []
