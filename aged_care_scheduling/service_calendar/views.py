from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from services.models import Service, BlockedTime
from residents.models import Resident
from homes.models import CareHome
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
import csv
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_http_methods
import json
from django.core.exceptions import ObjectDoesNotExist
from django.utils.dateparse import parse_datetime
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


@login_required
def calendar_view(request):
    caregivers = User.objects.filter(userprofile__role='staff').values('id', 'username')
    residents = Resident.objects.all()
    care_homes = CareHome.objects.all()
    return render(request, 'service_calendar/calendar.html', {
        'caregivers': caregivers,
        'residents': residents,
        'care_homes': care_homes,
    })

@login_required
def generate_report(request):
    report_type = request.GET.get('type', 'resident')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    services = Service.objects.filter(scheduled_time__range=[start_date, end_date])

    if report_type == 'resident':
        data = services.values('resident__first_name', 'resident__last_name', 'service_type__name').annotate(count=Count('id'))
    elif report_type == 'care_home':
        data = services.values('resident__care_home__name', 'service_type__name').annotate(count=Count('id'))
    else:  # group (assuming group is represented by care_home)
        data = services.values('resident__care_home__name', 'service_type__name').annotate(count=Count('id'))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_services_report.csv"'

    writer = csv.writer(response)
    if report_type == 'resident':
        writer.writerow(['Resident', 'Service Type', 'Count'])
        for item in data:
            writer.writerow([f"{item['resident__first_name']} {item['resident__last_name']}", item['service_type__name'], item['count']])
    else:
        writer.writerow(['Care Home', 'Service Type', 'Count'])
        for item in data:
            writer.writerow([item['resident__care_home__name'], item['service_type__name'], item['count']])

    return response

@login_required
def planner_view(request):
    caregivers = User.objects.filter(userprofile__role='staff').values('id', 'username')
    residents = Resident.objects.all()
    care_homes = CareHome.objects.all()
    
    return render(request, 'service_calendar/planner.html', {
        'caregivers': caregivers,
        'residents': residents,
        'care_homes': care_homes,
    })

@login_required
def get_events(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    caregiver_id = request.GET.get('caregiver')

    services = Service.objects.filter(
        scheduled_time__range=[start, end],
        status='scheduled'
    )

    if caregiver_id:
        services = services.filter(caregiver_id=caregiver_id)

    events = [{
        'id': service.id,
        'title': f"{service.service_type.name} - {service.resident.first_name} {service.resident.last_name}",
        'start': service.scheduled_time.isoformat(),
        'end': service.end_time.isoformat(),
        'extendedProps': {
            'serviceId': service.id,
            'resident': f"{service.resident.first_name} {service.resident.last_name}",
            'care_home': service.resident.care_home.name,
            'service_type': service.service_type.name,
            'caregiver': service.caregiver.username if service.caregiver else 'Unassigned',
            'status': service.status
        }
    } for service in services]

    return JsonResponse(events, safe=False)


def get_event_color(status):
    color_map = {
        'unscheduled': 'gray',
        'scheduled': 'blue',
        'completed': 'green',
        'not_completed': 'orange',
        'refused': 'purple',
        'missed': 'red'
    }
    return color_map.get(status, 'blue')

@login_required
@require_http_methods(["POST"])
def update_service(request):
    data = json.loads(request.body)
    try:
        service = Service.objects.get(id=data['id'])
        service.scheduled_time = parse_datetime(data['start'])
        service.end_time = parse_datetime(data['end'])
        service.caregiver_id = data.get('caregiver_id')
        
        if service.status == 'unscheduled':
            service.status = 'scheduled'
        
        service.save()
        
        return JsonResponse({
            'status': 'success',
            'id': service.id,
            'title': f"{service.service_type.name} - {service.resident.first_name} {service.resident.last_name}",
            'start': service.scheduled_time.isoformat(),
            'end': service.end_time.isoformat(),
            'color': get_event_color(service.status),
            'extendedProps': {
                'resident': f"{service.resident.first_name} {service.resident.last_name}",
                'care_home': service.resident.care_home.name,
                'service_type': service.service_type.name,
                'caregiver': service.caregiver.username if service.caregiver else 'Unassigned',
                'status': service.status
            }
        })
    except ObjectDoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Service not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def update_service_status(request):
    data = json.loads(request.body)
    try:
        service = Service.objects.get(id=data['id'])
        new_status = data['status']
        
        if new_status == 'completed':
            service.mark_as_completed()
        elif new_status == 'not_completed':
            reason = data.get('reason', '')
            service.mark_as_not_completed(reason)
        elif new_status == 'refused':
            service.mark_as_refused()
        
        return JsonResponse({
            'status': 'success',
            'id': service.id,
            'color': get_event_color(service.status),
            'extendedProps': {
                'status': service.status
            }
        })
    except ObjectDoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Service not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
@login_required
def get_unscheduled_services(request):
    date = request.GET.get('date')
    services = Service.objects.filter(
        Q(status='unscheduled', due_date=date) | 
        Q(status='unscheduled', scheduled_time__date=date)
    )
    data = [{
        'id': service.id,
        'title': f"{service.service_type.name} - {service.resident.first_name} {service.resident.last_name}",
        'duration': service.service_type.duration.total_seconds() / 3600  # Duration in hours
    } for service in services]
    return JsonResponse(data, safe=False)

@login_required
@require_http_methods(["POST"])
def create_service(request):
    data = json.loads(request.body)
    logger.debug(f"Received data: {data}")
    
    try:
        unscheduled_service_id = int(data.get('unscheduled_service_id'))
        logger.debug(f"Unscheduled service ID: {unscheduled_service_id}")
        
        caregiver_id = data.get('caregiver_id')
        if isinstance(caregiver_id, list):
            caregiver_id = caregiver_id[0]
        caregiver_id = int(caregiver_id) if caregiver_id else None
        
        start_time = parse_datetime(data['start'])
        end_time = parse_datetime(data['end'])

        unscheduled_service = Service.objects.get(id=unscheduled_service_id)

        # Check if a service already exists for this time slot
        existing_service = Service.objects.filter(
            caregiver_id=caregiver_id,
            scheduled_time=start_time,
            end_time=end_time
        ).first()

        if existing_service:
            return JsonResponse({'status': 'error', 'message': 'A service already exists for this time slot'}, status=400)

        unscheduled_service.scheduled_time = start_time
        unscheduled_service.end_time = end_time
        unscheduled_service.caregiver_id = caregiver_id
        unscheduled_service.status = 'scheduled'
        unscheduled_service.save()
        
        return JsonResponse({
            'status': 'success',
            'id': unscheduled_service.id,
            'title': f"{unscheduled_service.service_type.name} - {unscheduled_service.resident.first_name} {unscheduled_service.resident.last_name}",
            'start': unscheduled_service.scheduled_time.isoformat(),
            'end': unscheduled_service.end_time.isoformat(),
            'color': get_event_color(unscheduled_service.status),
            'extendedProps': {
                'resident': f"{unscheduled_service.resident.first_name} {unscheduled_service.resident.last_name}",
                'care_home': unscheduled_service.resident.care_home.name,
                'service_type': unscheduled_service.service_type.name,
                'caregiver': unscheduled_service.caregiver.username if unscheduled_service.caregiver else 'Unassigned',
                'status': unscheduled_service.status
            }
        })
    except ObjectDoesNotExist:
        logger.error(f"Service not found: {unscheduled_service_id}")
        return JsonResponse({'status': 'error', 'message': 'Service not found'}, status=404)
    except Exception as e:
        logger.error(f"Error creating service: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def unschedule_service(request):
    data = json.loads(request.body)
    service_id = data.get('service_id')

    try:
        service = Service.objects.get(id=service_id)
        service.status = 'unscheduled'
        service.scheduled_time = None
        service.end_time = None
        service.caregiver = None
        service.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Service unscheduled successfully'
        })
    except Service.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Service not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
        

@require_http_methods(["POST"])
def save_schedule(request):
    data = json.loads(request.body)
    date = timezone.datetime.fromisoformat(data['date'])
    services = data['services']

    try:
        for service_data in services:
            service = Service.objects.get(id=service_data['id'])
            start_time = parse_datetime(service_data['start'])
            end_time = parse_datetime(service_data['end'])
            caregiver_id = service_data.get('caregiver_id')  # Use .get() method

            service.scheduled_time = start_time
            service.end_time = end_time
            if caregiver_id:
                service.caregiver_id = caregiver_id
            service.status = 'scheduled'
            service.save()

        return JsonResponse({'status': 'success', 'message': 'Schedule saved successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)