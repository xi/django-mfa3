from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class MFAEnforceMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if (
            not getattr(view_func, 'mfa_public', False)
            and not request.path.startswith(settings.STATIC_URL)
            and request.user.is_authenticated
            and not request.user.mfakey_set.exists()
        ):
            return redirect('mfa:list')
