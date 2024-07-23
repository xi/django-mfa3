try:
    from stronghold.decorators import public as stronghold_login_not_required
except ImportError:
    def stronghold_login_not_required(view_func):
        return view_func

try:
    from django.contrib.auth.decorators import login_not_required
except ImportError:
    def login_not_required(view_func):
        return view_func


def public(view_func):
    view_func.mfa_public = True
    return view_func
