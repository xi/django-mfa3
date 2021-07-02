from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.http import HttpResponse
from django.urls import include
from django.urls import path

from mfa.decorators import public
from mfa.views import LoginView


def dummy(request):
    return HttpResponse(status=204)


urlpatterns = [
    path('', login_required(dummy)),
    path('login/', LoginView.as_view()),
    path('logout/', public(LogoutView.as_view(next_page='/'))),
    path('mfa/', include('mfa.urls', namespace='mfa')),
]
