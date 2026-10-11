"""Custom DRF permission classes for role-based access control."""
from rest_framework import permissions


class IsJournalistOrReadOnly(permissions.BasePermission):
    """
    Role-based permissions for articles.

    - Any authenticated user may read (GET, HEAD, OPTIONS).
    - Only journalists, editors, and publishers may create articles.
    - Only the author, editors, or publishers may modify/delete an article.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role in ('journalist', 'editor', 'publisher')

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.role in ('editor', 'publisher'):
            return True
        return obj.author == request.user