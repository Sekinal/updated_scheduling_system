from django.urls import reverse
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Resident, VisitHistory
from .forms import ResidentForm
from services.models import Service
from django.db.models import Count
from django.utils import timezone

class ResidentDetailView(DetailView):
    model = Resident
    template_name = 'resident/resident_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resident = self.get_object()
        if resident.care_home:
            context['back_url'] = reverse('care_homes:home_detail', kwargs={'pk': resident.care_home.pk})
        else:
            context['back_url'] = reverse('care_homes:home_list')
        return context

class ResidentCreateView(LoginRequiredMixin, CreateView):
    model = Resident
    form_class = ResidentForm
    template_name = 'resident/resident_form.html'

    def get_success_url(self):
        # Check if the resident is associated with a care home
        if 'care_home_id' in self.request.POST:
            care_home_id = self.request.POST['care_home_id']
            return reverse('care_homes:home_detail', kwargs={'pk': care_home_id})
        else:
            return reverse('care_homes:home_list')

class ResidentUpdateView(LoginRequiredMixin, UpdateView):
    model = Resident
    form_class = ResidentForm
    template_name = 'resident/resident_form.html'

    def get_success_url(self):
        # Check if the resident is associated with a care home
        if self.object.care_home:
            return reverse('care_homes:home_detail', kwargs={'pk': self.object.care_home.id})
        else:
            return reverse('care_homes:home_list')


class ResidentDeleteView(LoginRequiredMixin, DeleteView):
    model = Resident
    template_name = 'resident/resident_confirm_delete.html'
    
    def get_success_url(self):
        # Check if the resident is associated with a care home
        if self.object.care_home:
            return reverse('care_homes:home_detail', kwargs={'pk': self.object.care_home.id})
        else:
            return reverse('care_homes:home_list')

class ResidentDashboardView(DetailView):
    model = Resident
    template_name = 'resident/resident_dashboard.html'
    context_object_name = 'resident'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resident = self.get_object()

        # Get visit history
        context['visit_history'] = VisitHistory.objects.filter(resident=resident).select_related('service__service_type').order_by('-visit_time').distinct()

        # Get active services
        context['active_services'] = Service.objects.filter(resident=resident, status='scheduled').select_related('service_type').order_by('scheduled_time')

        # Get service frequency (count of completed services in the last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        context['service_frequency'] = VisitHistory.objects.filter(
            resident=resident,
            visit_time__gte=thirty_days_ago
        ).values('service__service_type__name').annotate(count=Count('id', distinct=True))

        # Add back_url
        if resident.care_home:
            context['back_url'] = reverse('care_homes:home_detail', kwargs={'pk': resident.care_home.pk})
        else:
            context['back_url'] = reverse('care_homes:home_list')

        return context