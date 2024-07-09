from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from .models import CareHome
from .forms import CareHomeForm
from residents.models import Resident
from django.core.paginator import Paginator

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class CareHomeListView(LoginRequiredMixin, ListView):
    model = CareHome
    template_name = 'care_homes/home_list.html'
    context_object_name = 'care_homes'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(address__icontains=search_query)
            )
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        
        # Filter active care homes
        active_care_homes = CareHome.objects.filter(is_active=True)
        
        # Get residents of active care homes
        residents = Resident.objects.filter(care_home__in=active_care_homes)
        
        # Paginate residents
        residents_paginator = Paginator(residents, 10)  # 10 residents per page
        residents_page = self.request.GET.get('residents_page')
        context['residents'] = residents_paginator.get_page(residents_page)
        
        return context

class CareHomeDetailView(DetailView):
    model = CareHome
    template_name = 'care_homes/home_detail.html'
    context_object_name = 'care_home'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        residents = self.object.residents.all()
        search_query = self.request.GET.get('search')
        if search_query:
            residents = residents.filter(Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query))
        
        paginator = Paginator(residents, 10)  # Show 10 residents per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['residents'] = page_obj
        context['search_query'] = search_query
        return context

class CareHomeCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = CareHome
    form_class = CareHomeForm
    template_name = 'care_homes/home_form.html'
    
    def get_success_url(self):
        return reverse_lazy('care_homes:home_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Care Home '{form.instance.name}' created successfully.")
        return super().form_valid(form)

class CareHomeUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = CareHome
    form_class = CareHomeForm
    template_name = 'care_homes/home_form.html'

    def get_success_url(self):
        return reverse_lazy('care_homes:home_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Care Home '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

class CareHomeDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = CareHome
    template_name = 'care_homes/home_confirm_delete.html'
    success_url = reverse_lazy('care_homes:home_list')
    context_object_name = 'care_home'

    def delete(self, request, *args, **kwargs):
        care_home = self.get_object()
        messages.success(request, f"Care Home '{care_home.name}' has been deleted.")
        return super().delete(request, *args, **kwargs)

def toggle_care_home_status(request, pk):
    care_home = get_object_or_404(CareHome, pk=pk)
    care_home.is_active = not care_home.is_active
    care_home.save()
    messages.success(request, f"Care home '{care_home.name}' has been {'activated' if care_home.is_active else 'deactivated'}.")
    return redirect('care_homes:home_detail', pk=pk)