from django.shortcuts import redirect


class MFAEnforceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if (
            not getattr(view_func, 'mfa_public', False)
            and request.user.is_authenticated
            and not request.user.mfakey_set.exists()
        ):
            return redirect('mfa:list')
