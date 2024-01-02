from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth import user_login_failed
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView
from django.views.generic import ListView

from . import settings
from .forms import MFAAuthForm
from .forms import MFACreateForm
from .mail import send_mail
from .mixins import MFAFormView, MFASessionDispatcher
from .models import MFAKey

try:
    from stronghold.views import StrongholdPublicMixin
except ImportError:
    from .mixins import DummyMixin as StrongholdPublicMixin


class LoginView(DjangoLoginView):
    def no_key_exists(self, form):
        return super().form_valid(form)

    def form_valid(self, form):
        user = form.get_user()
        if not user.mfakey_set.exists():
            return self.no_key_exists(form)

        mfa_session = getattr(self.request, "mfa_session", self.request.session)
        mfa_session['mfa_user'] = {
            'pk': user.pk,
            'backend': user.backend,
        }
        mfa_session['mfa_success_url'] = self.get_success_url()
        for method in settings.METHODS:
            if user.mfakey_set.filter(method=method).exists():
                return redirect('mfa:auth', method)


class MFARequiredIfExistsMixin(LoginRequiredMixin, MFASessionDispatcher):
    def dispatch(self, request, *args, **kwargs):
        self._get_mfa_session()
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        elif not self.mfa_session.get("mfa_authenticated") and request.user.mfakey_set.exists():
            # the user must be authenticated with a 2fa to access to this resource OR
            # he didn't have configured yet a new 2fa
            #
            # this prevents evasion attacks where an adversary being logged in without 2fa
            # is able to create a 2fa and/or delete a preexisting 2fa
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class MFAListView(MFARequiredIfExistsMixin, ListView):
    model = MFAKey

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class MFADeleteView(MFARequiredIfExistsMixin, DeleteView):
    model = MFAKey

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_success_url(self):
        return reverse('mfa:list')


class MFACreateView(LoginRequiredMixin, MFAFormView):
    form_class = MFACreateForm
    
    def get_template_names(self):
        return f'mfa/create_{self.method.name}.html'

    def get_success_url(self):
        return reverse('mfa:list')

    def begin(self):
        self._get_mfa_session()
        # the user can create new 2fa only if he doesn't have already configured a 2fa or if it is authenticated with 2fa
        if not self.request.user.mfakey_set.exists() or self.mfa_session.get("mfa_authenticated"):
            return self.method.register_begin(self.request.user)
        else:
            return self.handle_no_permission()
        
    def complete(self, code):
        mfa_completed = self.method.register_complete(self.challenge[1], code)
        if mfa_completed:
            self.mfa_session["mfa_authenticated"] = True
        return mfa_completed

    def form_valid(self, form):
        MFAKey.objects.create(
            user=self.request.user,
            method=self.method.name,
            name=form.cleaned_data['name'],
            secret=form.cleaned_data['secret'],
        )
        messages.success(self.request, _('Key was created successfully!'))
        return super().form_valid(form)


class MFAAuthView(StrongholdPublicMixin, MFAFormView):
    form_class = MFAAuthForm

    def dispatch(self, request, *args, **kwargs):
        self._get_mfa_session()
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return f'mfa/auth_{self.method.name}.html'

    def get_success_url(self):
        success_url = self.mfa_session.pop('mfa_success_url')
        if self.method.name == 'recovery':
            return reverse('mfa:list')
        else:
            return success_url

    @cached_property
    def user(self):
        try:
            user_data = self.mfa_session['mfa_user']
        except KeyError as e:
            raise Http404 from e
        User = get_user_model()
        user = get_object_or_404(User, pk=user_data['pk'])
        user.backend = user_data['backend']
        return user

    def begin(self):
        return self.method.authenticate_begin(self.user)

    def complete(self, code):
        mfa_auth = self.method.authenticate_complete(
            self.challenge[1], self.user, code,
        )
        self.mfa_session["mfa_authenticated"] = True
        return mfa_auth

    def form_invalid(self, form):
        user_login_failed.send(
            sender=__name__,
            credentials={'username': self.user.get_username()},
            request=self.request,
        )
        self.mfa_session["mfa_authenticated"] = False
        send_mail(self.user, self.method)
        return super().form_invalid(form)

    def form_valid(self, form):
        login(self.request, self.user)
        del self.mfa_session['mfa_user']
        return super().form_valid(form)
