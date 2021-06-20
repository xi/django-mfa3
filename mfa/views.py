from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DeleteView
from django.views.generic import ListView

from .models import MFAKey


class MFAListView(LoginRequiredMixin, ListView):
    model = MFAKey


class MFADeleteView(LoginRequiredMixin, DeleteView):
    model = MFAKey

    def get_success_url(self):
        return reverse('mfa:list')
