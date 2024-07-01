from django.db import models
from homes.models import CareHome

class Resident(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    care_home = models.ForeignKey(CareHome, on_delete=models.CASCADE, related_name='residents')
    admission_date = models.DateField(null=True)
    emergency_email = models.EmailField(null=True, blank=True, verbose_name='Emergency Contact Email')
    emergency_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Emergency Contact Phone')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class VisitHistory(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='visit_history')
    service = models.ForeignKey('services.Service', on_delete=models.CASCADE)
    visit_time = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.resident} - {self.service.service_type} at {self.visit_time}"