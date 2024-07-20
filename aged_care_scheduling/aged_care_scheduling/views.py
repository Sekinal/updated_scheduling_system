from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from services.models import Service, ServiceType
import json

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        next_month_start = (current_month_start + relativedelta(months=1))
        next_month_end = (next_month_start + relativedelta(months=1)) - relativedelta(days=1)

        # Current Month Statistics
        current_month_services = Service.objects.filter(scheduled_time__year=today.year, scheduled_time__month=today.month)
        context['current_month'] = today.strftime('%B %Y')
        context['current_month_due'] = current_month_services.count()
        context['current_month_completed'] = current_month_services.filter(status='completed').count()
        context['current_month_refused'] = current_month_services.filter(status='refused').count()

        # Following Month Statistics
        next_month_services = Service.objects.filter(scheduled_time__range=[next_month_start, next_month_end])
        context['next_month'] = next_month_start.strftime('%B %Y')
        context['next_month_due'] = next_month_services.count()
        context['next_month_hours_due'] = next_month_services.aggregate(
            total_hours=Sum('service_type__duration'))['total_hours'] or 0

        # Data for Service Type Distribution Chart
        service_type_data = ServiceType.objects.annotate(count=Count('service')).values('name', 'count')
        context['service_type_labels'] = json.dumps([item['name'] for item in service_type_data])
        context['service_type_counts'] = json.dumps([item['count'] for item in service_type_data])

        # Data for Service Status Chart
        status_data = current_month_services.values('status').annotate(count=Count('status'))
        context['status_labels'] = json.dumps([item['status'] for item in status_data])
        context['status_counts'] = json.dumps([item['count'] for item in status_data])

        # Data for Services Over Time Chart
        last_12_months = [(today - relativedelta(months=i)).strftime('%Y-%m') for i in range(11, -1, -1)]
        services_over_time = Service.objects.filter(
            scheduled_time__gte=today - relativedelta(months=12)
        ).annotate(month=TruncMonth('scheduled_time')).values('month').annotate(count=Count('id'))
        
        services_dict = {item['month'].strftime('%Y-%m'): item['count'] for item in services_over_time}
        context['services_over_time_labels'] = json.dumps(last_12_months)
        context['services_over_time_data'] = json.dumps([services_dict.get(month, 0) for month in last_12_months])

        return context