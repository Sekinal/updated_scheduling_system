# residents/views.py

from django.urls import reverse
import calendar
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from calendar import month_name

from .models import Resident
from .forms import ResidentForm
from services.models import Service, ServiceType, ResidentServiceFrequency
from django.db.models import Count
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
from accounts.models import UserProfile
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.db import transaction
from django.core.paginator import Paginator
from homes.models import CareHome
from datetime import timedelta
from services.forms import ResidentServiceFrequencyForm

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
            return reverse('residents:resident_detail', kwargs={'pk': care_home_id})
        else:
            return reverse('residents:resident_list')

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
        resident = self.object

        service_frequencies = ResidentServiceFrequency.objects.filter(resident=resident)
        context['service_frequencies'] = [
            {
                'id': sf.id,
                'service_type': sf.service_type,
                'recurrence_pattern_value': sf.recurrence_pattern,
                'frequency': sf.frequency,
                'start_date': sf.start_date,
                'end_date': sf.end_date,
                'start_time': sf.start_time,
                'end_time': sf.end_time,
            }
            for sf in service_frequencies
        ]
        
        # Form for adding new service frequency
        context['service_frequency_form'] = ResidentServiceFrequencyForm(resident=resident)
                
        # Visit history (completed, rescheduled, or not completed services)
        visit_history = Service.objects.filter(
            resident=resident,
            status__in=['completed', 'not_completed', 'refused']
        ).order_by('-scheduled_time')

        # Pagination for visit history
        paginator = Paginator(visit_history, 10)  # Show 10 services per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['visit_history'] = page_obj
        
        # Back URL
        if resident.care_home:
            context['back_url'] = reverse('care_homes:home_detail', kwargs={'pk': resident.care_home.pk})
        else:
            context['back_url'] = reverse('care_homes:home_list')
        
        return context

    def post(self, request, *args, **kwargs):
        resident = self.get_object()
        form = ResidentServiceFrequencyForm(request.POST, resident=resident)
        if form.is_valid():
            service_frequency = form.save(commit=False)
            service_frequency.resident = resident
            service_frequency.save()
            messages.success(request, 'Service frequency added successfully.')
            
            # Return updated service frequencies list
            service_frequencies = ResidentServiceFrequency.objects.filter(resident=resident)
            html = render_to_string('resident/service_frequency_list.html', {'service_frequencies': service_frequencies})
            return JsonResponse({'success': True, 'html': html})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

# residents/views.py

class ResidentListView(ListView):
    model = Resident
    template_name = 'resident/resident_list.html'
    context_object_name = 'residents'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', 'active')

        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(date_of_birth__icontains=search_query) |
                Q(admission_date__icontains=search_query) |
                Q(care_home__name__icontains=search_query)
            )

        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('last_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', 'active')
        return context

class ResidentServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'services/resident_service_list.html'
    context_object_name = 'services'
    paginate_by = 10

    def get_queryset(self):
        resident_id = self.kwargs.get('resident_id')
        queryset = Service.objects.filter(resident_id=resident_id)

        # Apply filters
        filters = Q()

        status = self.request.GET.get('status')
        if status:
            filters &= Q(status=status)

        service_type = self.request.GET.get('service_type')
        if service_type:
            filters &= Q(service_type_id=service_type)

        month = self.request.GET.get('month')
        if month:
            filters &= Q(scheduled_time__month=month)

        caregiver = self.request.GET.get('caregiver')
        if caregiver:
            if caregiver == 'unassigned':
                filters &= Q(caregiver__isnull=True)
            else:
                filters &= Q(caregiver_id=caregiver)

        return queryset.filter(filters).order_by('scheduled_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resident_id = self.kwargs.get('resident_id')
        context['resident'] = Resident.objects.get(id=resident_id)
        context['service_types'] = ServiceType.objects.all()
        context['months'] = [(i, month_name[i]) for i in range(1, 13)]
        context['caregivers'] = User.objects.filter(
            userprofile__role='staff',
            is_active=True
        ).select_related('userprofile')
        context['statuses'] = Service.SERVICE_STATUS

        # Preserve filter parameters
        context['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'service_type': self.request.GET.get('service_type', ''),
            'month': self.request.GET.get('month', ''),
            'caregiver': self.request.GET.get('caregiver', ''),
        }

        return context

class DeleteAllServicesView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        resident_id = kwargs.get('resident_id')
        resident = get_object_or_404(Resident, id=resident_id)

        services = Service.objects.filter(resident=resident)
        count = services.count()
        services.delete()

        messages.success(request, f"All {count} services for {resident.first_name} {resident.last_name} have been deleted.")
        return redirect('resident_service_list', resident_id=resident_id)
    
class ServiceFrequencyUpdateView(UpdateView):
    model = ResidentServiceFrequency
    fields = ['frequency', 'recurrence_pattern']
    template_name = 'resident/service_frequency_form.html'

    def get_success_url(self):
        return reverse_lazy('residents:resident_dashboard', kwargs={'pk': self.object.resident.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Service frequency updated successfully.')
        return super().form_valid(form)

class ServiceFrequencyDeleteView(DeleteView):
    model = ResidentServiceFrequency
    template_name = 'resident/service_frequency_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('residents:resident_dashboard', kwargs={'pk': self.object.resident.pk})

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Delete all related scheduled services
        Service.objects.filter(
            resident=self.object.resident,
            service_type=self.object.service_type,
            status='scheduled'
        ).delete()

        # Delete the service frequency
        self.object.delete()

        messages.success(self.request, 'Service frequency and all related scheduled services have been deleted.')
        return redirect(success_url)
    
class ResidentDeactivateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        resident = get_object_or_404(Resident, pk=pk)
        resident.deactivate()
        messages.success(request, f"{resident.first_name} {resident.last_name} has been deactivated.")
        return redirect('residents:resident_list')

class ResidentActivateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        resident = get_object_or_404(Resident, pk=pk)
        resident.activate()
        messages.success(request, f"{resident.first_name} {resident.last_name} has been activated.")
        return redirect('residents:resident_list')