from django.db import models
from homes.models import CareHome

class Schedule(models.Model):
    care_home = models.ForeignKey(CareHome, on_delete=models.CASCADE)
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Schedule for {self.care_home} on {self.date}"

class BlockedTime(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    reason = models.CharField(max_length=100)

    def __str__(self):
        return f"Blocked time on {self.schedule}: {self.start_time} - {self.end_time}"