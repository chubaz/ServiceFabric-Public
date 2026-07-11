from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsServiceOwnerForWrite(BasePermission):
    """Visibility is handled by the queryset; mutations require ownership or an explicit model permission."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if obj.owner_id == request.user.id:
            return True

        permission = 'api.delete_serviceinstance' if request.method == 'DELETE' else 'api.change_serviceinstance'
        return request.user.is_staff and request.user.has_perm(permission)
