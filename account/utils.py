from django.http import HttpResponseForbidden
from functools import wraps

def role_required(roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return HttpResponseForbidden("Login required")

            # ✅ ALLOW SUPERUSER ALWAYS
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # ✅ CHECK ROLE
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden("You are not allowed to access this page")

        return wrapper
    return decorator