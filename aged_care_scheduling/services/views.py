from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Service, ServiceType, ResidentPreference, BlockedTime, Escalation
from .forms import ServiceTypeForm, ServiceForm, ResidentPreferenceForm, BlockedTimeForm, EscalationForm
from residents.models import Resident
from django.urls import reverse
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.db import transaction
from django.views.generic import View
from django.utils import timezone
from .models import ResidentServiceFrequency
from .forms import ResidentServiceFrequencyForm

class ServiceTypeListView(LoginRequiredMixin, ListView):
    model = ServiceType
    template_name = 'services/service_type_list.html'
    context_object_name = 'service_types'
    paginate_by = 10  # Number of service types per page

    def get_queryset(self):
        return ServiceType.objects.all().order_by('name')

class ServiceTypeCreateView(LoginRequiredMixin, CreateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = 'services/service_type_form.html'
    success_url = reverse_lazy('service_type_list')

class ServiceTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = 'services/service_type_form.html'
    success_url = reverse_lazy('service_type_list')

class ServiceTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = ServiceType
    template_name = 'services/service_type_confirm_delete.html'
    success_url = reverse_lazy('service_type_list')

class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'

    def get_initial(self):
        initial = super().get_initial()
        resident_id = self.request.GET.get('resident_id')
        if resident_id:
            initial['resident'] = get_object_or_404(Resident, pk=resident_id)
        return initial

    def get_success_url(self):
        if self.object.resident:
            return reverse_lazy('residents:resident_dashboard', kwargs={'pk': self.object.resident.pk})
        else:
            return reverse_lazy('service_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Service scheduled successfully for {self.object.resident}")
        return response    
class DeleteAllServicesView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        Service.objects.all().delete()
        messages.success(request, "All services have been deleted.")
        return redirect(reverse_lazy('service_list'))
    
class ServiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'

    def get_success_url(self):
        if self.object.resident:
            return reverse_lazy('residents:resident_dashboard', kwargs={'pk': self.object.resident.pk})
        else:
            return reverse_lazy('service_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Service updated successfully for {self.object.resident}")
        return response
class ServiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Service
    template_name = 'services/service_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('residents:resident_dashboard', kwargs={'pk': self.object.resident.pk})

class ServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    paginate_by = 10

    def get_queryset(self):
        return Service.objects.filter(
            scheduled_time__gte=timezone.now()
        ).order_by('scheduled_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pagination for services
        services = self.get_queryset()
        service_paginator = Paginator(services, self.paginate_by)
        service_page = self.request.GET.get('page')
        context['services'] = service_paginator.get_page(service_page)

        # Fetch all blocked times
        all_blocked_times = BlockedTime.objects.all().order_by('start_time')
        
        # Pagination for blocked times
        blocked_paginator = Paginator(all_blocked_times, 10)  # 10 blocked times per page
        blocked_page = self.request.GET.get('blocked_page')
        context['blocked_times'] = blocked_paginator.get_page(blocked_page)

        return context
class ResidentServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'services/resident_service_list.html'
    context_object_name = 'services'
    paginate_by = 10

    def get_queryset(self):
        self.resident = get_object_or_404(Resident, pk=self.kwargs['resident_id'])
        return Service.objects.filter(resident=self.resident).order_by('due_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resident'] = self.resident
        return context

class ResidentPreferenceCreateView(LoginRequiredMixin, CreateView):
    model = ResidentPreference
    form_class = ResidentPreferenceForm
    template_name = 'services/resident_preference_form.html'
    success_url = reverse_lazy('resident_preference_list')

class ResidentPreferenceListView(LoginRequiredMixin, ListView):
    model = ResidentPreference
    template_name = 'services/resident_preference_list.html'
    context_object_name = 'preferences'

class BlockedTimeListView(LoginRequiredMixin, ListView):
    model = BlockedTime
    template_name = 'services/blocked_times.html'
    context_object_name = 'blocked_times'
    paginate_by = 10

class BlockedTimeCreateView(LoginRequiredMixin, CreateView):
    model = BlockedTime
    form_class = BlockedTimeForm
    template_name = 'services/blocked_time_form.html'
    success_url = reverse_lazy('blocked_time_list')

class BlockedTimeUpdateView(LoginRequiredMixin, UpdateView):
    model = BlockedTime
    form_class = BlockedTimeForm
    template_name = 'services/blocked_time_form.html'
    success_url = reverse_lazy('blocked_time_list')

class BlockedTimeDeleteView(LoginRequiredMixin, DeleteView):
    model = BlockedTime
    template_name = 'services/blocked_time_confirm_delete.html'
    success_url = reverse_lazy('blocked_time_list')
    
class ServiceStatusUpdateView(LoginRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_status_update.html'

    def form_valid(self, form):
        service = form.save(commit=False)
        
        if service.status == 'completed':
            service.mark_as_completed()
            messages.success(self.request, f"Service for {service.resident} has been marked as completed.")
        elif service.status == 'refused':
            service.mark_as_refused()
            messages.warning(self.request, f"Service for {service.resident} has been marked as refused.")
        elif service.status == 'not_completed':
            rescheduled_service = service.mark_as_not_completed(service.reschedule_reason)
            if rescheduled_service:
                messages.info(self.request, f"Service for {service.resident} has been marked as not completed and rescheduled to {rescheduled_service.scheduled_time}.")
            else:
                messages.warning(self.request, f"Service for {service.resident} has been marked as not completed but could not be rescheduled.")
        
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the service status. Please check the form and try again.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('residents:resident_dashboard', kwargs={'pk': self.object.resident.pk})


class EscalationListView(LoginRequiredMixin, ListView):
    model = Escalation
    template_name = 'services/escalation_list.html'
    context_object_name = 'escalations'
    paginate_by = 10

    def get_queryset(self):
        return Escalation.objects.all().order_by('-date_created')

class EscalationUpdateView(LoginRequiredMixin, UpdateView):
    model = Escalation
    form_class = EscalationForm
    template_name = 'services/escalation_update.html'
    success_url = reverse_lazy('escalation_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        escalation = self.object
        if escalation.resolved:
            messages.success(self.request, f"Escalation for {escalation.resident} has been resolved.")
        return response

def check_missed_services(request):
    Service.check_missed_services()
    messages.info(request, "Missed services have been checked and escalated if necessary.")
    return redirect('service_list')

def edit_service_frequency(request, pk):
    service_frequency = get_object_or_404(ResidentServiceFrequency, pk=pk)
    if request.method == 'POST':
        form = ResidentServiceFrequencyForm(request.POST, instance=service_frequency, resident=service_frequency.resident)
        if form.is_valid():
            service_frequency = form.save()
            
            # Delete existing future services
            Service.objects.filter(
                resident=service_frequency.resident,
                service_type=service_frequency.service_type,
                status__in=['unscheduled', 'scheduled'],
                due_date__gte=timezone.now().date()
            ).delete()
            
            # Create new services based on updated frequency
            service_frequency.create_services()
            
            messages.success(request, 'Service frequency updated successfully and services rescheduled.')
            return redirect('residents:resident_dashboard', pk=service_frequency.resident.pk)
    else:
        form = ResidentServiceFrequencyForm(instance=service_frequency, resident=service_frequency.resident)
    
    return render(request, 'services/edit_service_frequency.html', {'form': form, 'service_frequency': service_frequency})
def delete_service_frequency(request, pk):
    service_frequency = get_object_or_404(ResidentServiceFrequency, pk=pk)
    resident_pk = service_frequency.resident.pk
    service_frequency.delete()  # This will now delete related services as well
    messages.success(request, 'Service frequency and related uncompleted services deleted successfully.')
    return redirect('residents:resident_dashboard', pk=resident_pk)

def add_service_frequency(request, resident_id):
    resident = get_object_or_404(Resident, pk=resident_id)
    if request.method == 'POST':
        form = ResidentServiceFrequencyForm(request.POST, resident_id=resident_id)
        if form.is_valid():
            service_frequency = form.save()
            service_frequency.create_services()  # Create the actual service instances
            messages.success(request, f"Service frequency added successfully for {resident.full_name}")
            return redirect(reverse('residents:resident_dashboard', kwargs={'pk': resident_id}))
    else:
        form = ResidentServiceFrequencyForm(resident_id=resident_id)
    
    context = {
        'form': form,
        'resident': resident,
    }
    return render(request, 'services/add_service_frequency.html', context)