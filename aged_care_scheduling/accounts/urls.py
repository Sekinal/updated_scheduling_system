from django.urls import path
from .views import CustomLoginView, CustomLogoutView, CustomPasswordChangeView, password_change_done

app_name = 'accounts'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', password_change_done, name='password_change_done'),
]