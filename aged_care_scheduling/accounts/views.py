from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    success_url = reverse_lazy('')

class CustomLogoutView(LoginRequiredMixin, LogoutView):
    next_page = reverse_lazy('accounts:login')

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:password_change_done')

def password_change_done(request):
    return render(request, 'accounts/password_change_done.html')