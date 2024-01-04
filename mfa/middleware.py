import time

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.utils.cache import patch_vary_headers
from django.utils.http import http_date

from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.middleware import SessionMiddleware


class MFAEnforceMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if (
            not getattr(view_func, 'mfa_public', False)
            and request.user.is_authenticated
            and not request.user.mfakey_set.exists()
        ):
            return redirect('mfa:list')


class MfaSessionMiddleware(SessionMiddleware):
    cookie_name = getattr(settings, "MFA_COOKIE_NAME", "mfa_session")
    
    def process_request(self, request):
        session_key = request.COOKIES.get(self.cookie_name, None)
        request.mfa_session = self.SessionStore(session_key)
    
    def process_response(self, request, response):
        """
        If request.mfa_session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie or delete
        the session cookie if the session has been emptied.
        """
        try:
            accessed = request.mfa_session.accessed
            modified = request.mfa_session.modified
            empty = request.mfa_session.is_empty()
        except AttributeError:
            return response
        # First check if we need to delete this cookie.
        # The session should be deleted only if the session is entirely empty.
        if self.cookie_name in request.COOKIES and empty:
            response.delete_cookie(
                self.cookie_name,
                path=settings.SESSION_COOKIE_PATH,
                domain=settings.SESSION_COOKIE_DOMAIN,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )
            patch_vary_headers(response, ("Cookie",))
        else:
            if accessed:
                patch_vary_headers(response, ("Cookie",))
            # relies and the global one
            if (modified or settings.SESSION_SAVE_EVERY_REQUEST) and not empty:
                if request.mfa_session.get_expire_at_browser_close():
                    max_age = None
                    expires = None
                else:
                    max_age = request.mfa_session.get_expiry_age()
                    expires_time = time.time() + max_age
                    expires = http_date(expires_time)
                # Save the session data and refresh the client cookie.
                # Skip session save for 500 responses, refs #3881.
                if response.status_code != 500:
                    try:
                        request.mfa_session.save()
                    except UpdateError:
                        raise SuspiciousOperation(
                            "The request's session was deleted before the "
                            "request completed. The user may have logged "
                            "out in a concurrent request, for example."
                        )
                    response.set_cookie(
                        self.cookie_name,
                        request.mfa_session.session_key,
                        max_age=max_age,
                        expires=expires,
                        domain=settings.SESSION_COOKIE_DOMAIN,
                        path=settings.SESSION_COOKIE_PATH,
                        secure=settings.SESSION_COOKIE_SECURE or None,
                        httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                        samesite=settings.SESSION_COOKIE_SAMESITE,
                    )
        return response
