from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from services.models import Service

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_services'] = Service.objects.order_by('-scheduled_time')[:5]
        context['upcoming_services'] = Service.objects.filter(status='scheduled').order_by('scheduled_time')[:5]
        return context