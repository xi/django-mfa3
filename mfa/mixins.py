from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView

from . import fido2
from . import totp


class DummyMixin:
    pass


class MFAFormView(FormView):
    @property
    def method(self):
        if self.kwargs['method'] == 'FIDO2':
            return fido2
        elif self.kwargs['method'] == 'TOTP':
            return totp
        else:
            raise Http404

    def get_state(self):
        try:
            return self.request.session['mfa_state']
        except KeyError as e:
            raise Http404 from e

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mfa_data'], self.request.session['mfa_state'] = self.begin()
        return context

    def get_form(self):
        form = super().get_form()
        form.complete = self.complete
        return form

    def form_valid(self, form):
        del self.request.session['mfa_state']
        return super().form_valid(form)
