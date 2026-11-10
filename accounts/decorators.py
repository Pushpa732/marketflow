from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def seller_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_seller:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper



def customer_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_customer:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper