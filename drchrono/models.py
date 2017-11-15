from __future__ import division

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from dateutil import tz
from datetime import timedelta
from localflavor.us.us_states import US_STATES

from api import patch_appointment

class Patient(models.Model):
    # info form
    GENDER_CHOICES = (
        ('Male,', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )

    ETHNICITY_CHOICES = (
        ('blank', ''),
        ('hispanic', 'Hispanic'),
        ('not_hispanic', 'Not Hispanic'),
        ('declined', 'Decline to self-identify'),
    )
    RACE_CHOICES = (
        ('blank', ''),
        ('indian', 'Indian'),
        ('asian', 'Asian'),
        ('black', 'Black'),
        ('hawaiian', 'Hawaiian'),
        ('white', 'White'),
        ('declined', 'Decline to self-identify'),
    )

    STATE_CHOICES = US_STATES

    patient_id = models.PositiveIntegerField()
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    ssn = models.CharField(max_length=256)
    image_link = models.CharField(max_length=200, default='https://i.ytimg.com/vi/tntOCGkgt98/maxresdefault.jpg')

    updated_at = models.DateTimeField()

    dob = models.DateTimeField(blank=True, null=True)
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES, blank=True, null=True)
    race = models.CharField(max_length=50, choices=RACE_CHOICES, blank=True, null=True)
    ethnicity = models.CharField(max_length=50, choices=ETHNICITY_CHOICES, blank=True, null=True)

    address = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    zipcode = models.CharField(max_length=10, blank=True, null=True)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, blank=True, null=True)

    cell_phone = models.CharField(max_length=30, blank=True, null=True)
    home_phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.CharField(max_length=60, blank=True, null=True)

    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return '{self.first_name} {self.last_name}'.format(self=self)


class Doctor(models.Model):
    doctor_user = models.OneToOneField(User)
    doctor_id = models.PositiveIntegerField()
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    office_name = models.CharField(max_length=100, default='Office A')
    office_phone = models.CharField(max_length=100, default='000-000-0000')
    kiosk_key = models.CharField(max_length=50, default='disable_kiosk')

    def __str__(self):
        return '{self.first_name} {self.last_name}'.format(self=self)

class AppointmentQuerySet(models.QuerySet):
    def get_appointments(self, date, checked_in, seen, completed):
        if checked_in is not None:
            return self.filter(scheduled_date=date, checked_in=checked_in)
        elif seen is not None:
            return self.filter(scheduled_date=date, seen=seen)
        elif completed is not None:
            return self.filter(scheduled_date=date, completed=completed)
        return self.filter(scheduled_date=date)

    def not_yet_arrived(self):
        today_date = timezone.localtime(timezone.now()).date
        return self.filter(checked_in=False, scheduled_date=today_date)

    def checked_in(self):
        return self.filter(checked_in=True)

    def seen(self):
        return self.filter(checked_in=True, seen=True)

    def completed(self):
        return self.filter(checked_in=True, seen=True, completed=True)

    def filter_by_patient(self, pid):

        return self.filter(id =pid)


class AppointmentManager(models.Manager):
    def get_queryset(self):
        return AppointmentQuerySet(self.model, using=self.db)

    def get_appointments(self, date=timezone.localtime(timezone.now()).date, checked_in=None, seen=None, completed=None):
        appts = self.get_queryset().get_appointments(date, checked_in, seen, completed)
        retAppts = []
        for appt in appts:
            checked_in_time = None
            seen_at_time = None
            completed_at_time = None
            if appt.checked_in_time is not None:
                checked_in_time = appt.checked_in_time.isoformat()
            if appt.seen_at_time is not None:
                seen_at_time = appt.seen_at_time.isoformat()
            if appt.completed_at_time is not None:
                completed_at_time = appt.completed_at_time.isoformat()
            retAppts.append({
                'id': appt.id,
                'first_name': appt.patient.first_name,
                'last_name': appt.patient.last_name,
                'picture': appt.patient.image_link,
                'scheduled_time': appt.scheduled_time.astimezone(
                    tz.gettz(timezone.get_default_timezone_name())).isoformat(),
                'reason': appt.reason,
                'status': appt.status,
                'checked_in': appt.checked_in,
                'seen': appt.seen,
                'completed': appt.completed,
                'checked_in_time': checked_in_time,
                'seen_at_time': seen_at_time,
                'completed_at_time': completed_at_time,
                'duration': appt.duration,
                'sch_time_datetime': appt.scheduled_time,
            })
        return retAppts

    def not_yet_arrived(self):
        return self.get_queryset().not_yet_arrived()

    def checked_in(self):
        return self.get_queryset().checked_in()

    def seen(self):
        return self.get_queryset().seen()

    def completed(self):
        return self.get_queryset().completed()

    def filter_by_patient(self, pid):
        return self.get_queryset().filter_by_patient(pid)


class Appointment(models.Model):
    appointment_id = models.PositiveIntegerField()
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, editable=False, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, editable=False, blank=True)
    scheduled_time = models.DateTimeField()
    scheduled_date = models.DateField()
    duration = models.IntegerField(default=0)
    is_walk_in = models.BooleanField()
    reason = models.CharField(max_length=200, blank=True, null=True)

    # check in, seen time
    status = models.CharField(max_length=50, default='Not yet arrived')
    checked_in = models.BooleanField(default=False)
    seen = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    checked_in_time = models.DateTimeField(blank=True, null=True)
    seen_at_time = models.DateTimeField(blank=True, null=True)
    completed_at_time = models.DateTimeField(blank=True, null=True)

    objects = AppointmentManager()

    def checked_in_func(self, request):
        response = patch_appointment(request, self.appointment_id, {'status': 'Arrived'})
        if response.status_code < 400:
            self.checked_in = True
            self.status = 'Checked in'
            self.checked_in_time = timezone.now()
            self.save()
            return True
        else:
            return False

    def seen_func(self, request):
        response = patch_appointment(request, self.appointment_id, {'status': 'In Session'})
        if response.status_code < 400:
            self.seen = True
            self.status = 'Currently in session'
            self.seen_at_time = timezone.now()
            self.save()
            return True
        else:
            return False

    def completed_func(self, request):
        response = patch_appointment(request, self.appointment_id, {'status': 'Complete'})
        if response.status_code < 400:
            self.completed = True
            self.status = 'Completed appointment'
            self.completed_at_time = timezone.now()
            self.save()
            return True
        else:
            return False

    def save(self, *args, **kwargs):
        super(Appointment, self).save(*args, **kwargs)

    def waiting_time(self):
        if self.seen:
            return (self.seen_at_time - self.checked_in_time).seconds
        else:
            return (timezone.now() - self.checked_in_time).seconds

    @classmethod
    def avg_waiting_time(cls):
        appts = cls.objects.all()
        total_waiting_time = timedelta(0)
        count = 0
        for appt in appts:
            if appt.seen_at_time is not None:
                total_waiting_time += appt.seen_at_time - appt.checked_in_time
                count += 1
            elif appt.checked_in_time is not None:
                total_waiting_time += timezone.now() - appt.checked_in_time
                count += 1
        total_waiting_time = total_waiting_time.microseconds + \
                 1000000 * (total_waiting_time.seconds + 86400 * total_waiting_time.days)
        if count > 0:
            return total_waiting_time // (count*1000)
        return 0

    def __str__(self):
        return '{}, {}, {}'.format(self.doctor, self.patient, self.scheduled_time)

class WebhookTransaction(models.Model):
    UNPROCESSED = 1
    PROCESSED = 2
    ERROR = 3

    STATUSES = (
        (UNPROCESSED, 'Unprocessed'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    )

    date_generated = models.DateTimeField()
    date_received = models.DateTimeField(default=timezone.now)
    body = models.CharField(max_length=3000)
    request_meta = models.CharField(max_length=3000)
    model = models.CharField(max_length=100)
    status = models.CharField(max_length=250, choices=STATUSES, default=UNPROCESSED)

    def __unicode__(self):
        return u'{0}'.format(self.date_event_generated)