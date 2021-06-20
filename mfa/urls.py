from django.urls import path

from .views import MFADeleteView
from .views import MFAListView

app_name = 'mfa'
urlpatterns = [
    path('', MFAListView.as_view(), name='list'),
    path('<int:pk>/delete/', MFADeleteView.as_view(), name='delete'),
]
