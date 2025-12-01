# file_storage_app/permissions.py

from rest_framework import permissions
from django.shortcuts import get_object_or_404
from files.models import Organization


class IsFileUploaderOrganization(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        if request.method == 'POST':
            org_id = view.kwargs.get('org_id')
            if not org_id:
                return False
            try:
                organization = get_object_or_404(Organization, pk=org_id)
            except Exception:
                return False
            return request.user.is_authenticated and request.user.organization == organization
        return request.user.is_authenticated
