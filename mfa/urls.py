from django.urls import path

from .decorators import public
from .views import MFAAuthView
from .views import MFACreateView
from .views import MFADeleteView
from .views import MFAListView

app_name = 'mfa'
urlpatterns = [
    path('', public(MFAListView.as_view()), name='list'),
    path('<int:pk>/delete/', public(MFADeleteView.as_view()), name='delete'),
    path('create/<method>/', public(MFACreateView.as_view()), name='create'),
    path('auth/<method>/', MFAAuthView.as_view(), name='auth'),
]
