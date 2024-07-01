from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Service, ServiceType, ResidentPreference, BlockedTime, Escalation
from .forms import ServiceTypeForm, ServiceForm, ResidentPreferenceForm, BlockedTimeForm, EscalationForm
from residents.models import Resident
from django.core.paginator import Paginator
from django.db.models import Q

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
    success_url = reverse_lazy('service_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        service = self.object
        if service.status == 'refused':
            messages.warning(self.request, f"Service for {service.resident} has been marked as refused.")
        elif service.status == 'not_completed':
            messages.info(self.request, f"Service for {service.resident} has been marked as not completed and rescheduled.")
        return response

class ServiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'
    success_url = reverse_lazy('service_list')

    def form_valid(self, form):
        old_status = self.object.status
        response = super().form_valid(form)
        service = self.object
        if service.status != old_status:
            if service.status == 'completed':
                messages.success(self.request, f"Service for {service.resident} has been marked as completed.")
            elif service.status == 'refused':
                messages.warning(self.request, f"Service for {service.resident} has been marked as refused.")
            elif service.status == 'not_completed':
                messages.info(self.request, f"Service for {service.resident} has been marked as not completed and rescheduled.")
        return response

class ServiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Service
    template_name = 'services/service_confirm_delete.html'
    success_url = reverse_lazy('service_list')

class ServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    paginate_by = 10  # Number of services per page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pagination for services
        services = self.get_queryset()
        service_paginator = Paginator(services, self.paginate_by)
        service_page = self.request.GET.get('page')
        context['services'] = service_paginator.get_page(service_page)

        # Fetch all blocked times
        all_blocked_times = BlockedTime.objects.all().order_by('start_time')
        
        # Add debug information
        context['blocked_times_count'] = all_blocked_times.count()
        context['all_blocked_times'] = all_blocked_times

        # Pagination for blocked times
        blocked_paginator = Paginator(all_blocked_times, 10)  # 10 blocked times per page
        blocked_page = self.request.GET.get('blocked_page')
        context['blocked_times'] = blocked_paginator.get_page(blocked_page)

        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(service_type__name__icontains=search_query) |
                Q(resident__first_name__icontains=search_query) |
                Q(resident__last_name__icontains=search_query)
            )
        return queryset.order_by('-scheduled_time')  # Changed to descending order

class ResidentServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'services/resident_service_list.html'
    context_object_name = 'services'

    def get_queryset(self):
        resident_id = self.kwargs['resident_id']
        return Service.objects.filter(resident__id=resident_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resident'] = get_object_or_404(Resident, id=self.kwargs['resident_id'])
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

class BlockedTimeCreateView(LoginRequiredMixin, CreateView):
    model = BlockedTime
    form_class = BlockedTimeForm
    template_name = 'services/blocked_time_form.html'
    success_url = reverse_lazy('blocked_time_list')

class BlockedTimeListView(LoginRequiredMixin, ListView):
    model = BlockedTime
    template_name = 'services/blocked_time_list.html'
    context_object_name = 'blocked_times'

class BlockedTimeUpdateView(LoginRequiredMixin, UpdateView):
    model = BlockedTime
    form_class = BlockedTimeForm
    template_name = 'services/blocked_time_form.html'
    success_url = reverse_lazy('service_list')

class BlockedTimeDeleteView(LoginRequiredMixin, DeleteView):
    model = BlockedTime
    template_name = 'services/blocked_time_confirm_delete.html'
    success_url = reverse_lazy('service_list')
    
class ServiceStatusUpdateView(LoginRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_status_update.html'
    success_url = reverse_lazy('service_list')

    def form_valid(self, form):
        old_status = self.object.status
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
        messages.success(self.request, "Service status updated successfully.")
        return reverse_lazy('service_list')


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