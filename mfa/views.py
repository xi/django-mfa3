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
from .mixins import MFAFormView
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

        self.request.session['mfa_user'] = {
            'pk': user.pk,
            'backend': user.backend,
        }
        self.request.session['mfa_success_url'] = self.get_success_url()
        for method in settings.METHODS:
            if user.mfakey_set.filter(method=method).exists():
                return redirect('mfa:auth', method)


class MFAListView(LoginRequiredMixin, ListView):
    model = MFAKey

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class MFADeleteView(LoginRequiredMixin, DeleteView):
    model = MFAKey

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_success_url(self):
        return reverse('mfa:list')


class MFACreateView(LoginRequiredMixin, MFAFormView):
    form_class = MFACreateForm

    def get_template_names(self):
        return 'mfa/create_%s.html' % self.method.name

    def get_success_url(self):
        return reverse('mfa:list')

    def begin(self):
        return self.method.register_begin(self.request.user)

    def complete(self, code):
        return self.method.register_complete(self.challenge[1], code)

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

    def get_template_names(self):
        return 'mfa/auth_%s.html' % self.method.name

    def get_success_url(self):
        success_url = self.request.session.pop('mfa_success_url')
        if self.method.name == 'recovery':
            return reverse('mfa:list')
        else:
            return success_url

    @cached_property
    def user(self):
        try:
            user_data = self.request.session['mfa_user']
        except KeyError as e:
            raise Http404 from e
        User = get_user_model()
        user = get_object_or_404(User, pk=user_data['pk'])
        user.backend = user_data['backend']
        return user

    def begin(self):
        return self.method.authenticate_begin(self.user)

    def complete(self, code):
        return self.method.authenticate_complete(
            self.challenge[1], self.user, code,
        )

    def form_invalid(self, form):
        user_login_failed.send(
            sender=__name__,
            credentials={'username': self.user.get_username()},
            request=self.request,
        )
        send_mail(self.user, self.method)
        return super().form_invalid(form)

    def form_valid(self, form):
        login(self.request, self.user)
        del self.request.session['mfa_user']
        return super().form_valid(form)
