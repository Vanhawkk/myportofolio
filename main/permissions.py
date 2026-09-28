from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


LOGIN_URL = "main:login"


def superuser_required(view_func):
    """Allow only authenticated superusers to access a view."""

    @login_required(login_url=LOGIN_URL)
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied

        return view_func(request, *args, **kwargs)

    return wrapped_view


def editor_or_superuser_required(permission):
    """Allow superusers or authenticated users with a change permission."""

    def decorator(view_func):
        @login_required(login_url=LOGIN_URL)
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not (
                request.user.is_superuser
                or request.user.has_perm(permission)
            ):
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator
