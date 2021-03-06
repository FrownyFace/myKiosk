from django.core.urlresolvers import reverse
from django.shortcuts import redirect

import hashlib
import pytz
from dateutil import parser
from datetime import timedelta

from schedule.models import Calendar
from schedule.models import Event
from schedule.models import Rule

from api import Endpoint, URL_ROOT
from models import *
from forms import VerifyForm


def update_local(request):
    e = Endpoint(request)
    url = "{}/patients".format(URL_ROOT)
    params = {"doctor_id": request.user}
    patients = e.get(url, params)
    create_patients_local(patients['results'])

    url = "{}/appointments".format(URL_ROOT)
    params = {"date": timezone.localtime(timezone.now()).date().isoformat()}
    appointments = e.get(url, params)
    create_appointments_local(appointments['results'], request.user)


def create_patients_local(patients):
    for patient in patients:
        cur_p = Patient.objects.filter(patient_id=int(patient['id']))
        if not cur_p:
            p = {'patient_id': int(patient['id']),
                 'first_name': patient['first_name'],
                 'last_name': patient['last_name'],
                 'ssn': hashlib.sha256(patient['social_security_number'][-4:]).hexdigest(),
                 'image_link': patient['patient_photo'],
                 'updated_at': timeformater(patient['updated_at']),
                 'dob': timeformater(patient['date_of_birth']),
                 'gender': patient['gender'],
                 'race': patient['race'],
                 'ethnicity': patient['ethnicity'],
                 'address': patient['address'],
                 'city': patient['city'],
                 'zipcode': patient['zip_code'],
                 'state': patient['state'],
                 'cell_phone': patient['cell_phone'],
                 'home_phone': patient['home_phone'],
                 'email': patient['email'],
                 'emergency_contact_name': patient['emergency_contact_name'],
                 'emergency_contact_phone': patient['emergency_contact_phone'],
                 }
            Patient.objects.create(**p)

        #elif cur_p[0].updated_at <= timeformater(patient['updated_at']):
        #    print('update patient stuff')


def create_appointments_local(appointments, doctor):
    for appt in appointments:
        if not Appointment.objects.filter(appointment_id=int(appt['id'])):
            dt = timeformater(appt['scheduled_time'])
            checked_in = False
            seen = False
            completed = False
            checked_in_time = None
            seen_at_time = None
            completed_at_time = None
            status = 'Not yet arrived'
            print(appt['status'])
            if appt['status'] == 'Arrived':
                checked_in = True
                status = 'Checked in'
                checked_in_time = dt
            elif appt['status'] == 'In Session':
                checked_in = True
                seen = True
                status = 'Currently in session'
                seen_at_time = dt
            elif appt['status'] == 'Complete':
                checked_in = True
                seen = True
                completed = True
                status = 'Completed appointment'
                completed_at_time = dt + timedelta(minutes=int(appt['duration']))
            appt = {
                'appointment_id': int(appt['id']),
                'doctor': Doctor.objects.get(doctor_user=doctor),
                'patient': Patient.objects.get(patient_id=int(appt['patient'])),
                'scheduled_time': dt,
                'scheduled_date': dt.date(),
                'is_walk_in': 'True' == appt['is_walk_in'],
                'reason': appt['reason'],
                'status': status,
                'checked_in': checked_in,
                'seen': seen,
                'completed': completed,
                'checked_in_time': checked_in_time,
                'seen_at_time': seen_at_time,
                'completed_at_time': completed_at_time,
                'duration': appt['duration'],
                }
            Appointment.objects.create(**appt)
            update_calendar(appt)


def find_doctor(request):
    e = Endpoint(request)
    url = "{}/users/current".format(URL_ROOT)
    doctor_id = e.get(url)['doctor']
    url = "{}/doctors/{}".format(URL_ROOT, doctor_id)
    doctor = e.get(url)
    return doctor

def add_doctor(request, form_info):
    d = {
        'first_name': form_info['first_name'],
        'last_name': form_info['last_name'],
        'office_name': form_info['office_name'],
        'doctor_id': int(form_info['doctor_id']),
        'doctor_user': request.user
    }
    try:
        Doctor.objects.create(**d)
        return True
    except:
        return False

def update_doctor(request, doctor, form_info):
    doctor.first_name = form_info['first_name']
    doctor.last_name = form_info['last_name']
    doctor.office_name = form_info['office_name']
    doctor.office_phone = form_info['office_phone']
    doctor.kiosk_key = form_info['kiosk_key']
    try:
        doctor.save()
        return True
    except:
        return False

    #e = Endpoint(request)
    #url = "{}/doctors/{}".format(URL_ROOT, doctor.doctor_id)
    #e.patch(url, payload={
    #    'first_name': form_info['first_name'],
    #    'last_name': form_info['last_name'],
    #})

def get_all_daily_appointments(request):
    e = Endpoint(request)
    url = "{}/appointments".format(URL_ROOT)
    params = {"date": timezone.localtime(timezone.now()).date().isoformat()}
    appts = e.get(url, params)
    return appts


def find_patient(request, params):
    e = Endpoint(request)
    url = "{}/patients".format(URL_ROOT)
    all_patients = []
    while url:
        response = e.get(url, params)
        all_patients.extend(response['results'])
        url = response['next']
    return all_patients

def find_patient_local(params):
    patient = Patient.objects.filter(first_name=params['first_name'], last_name=params['last_name'])
    if len(patient) == 0:
        return False
    return patient[0]

def find_appts_by_patient_local(patient):
    appts = Appointment.objects.filter(patient=patient,
                                       scheduled_date=timezone.localtime(timezone.now()).date(), checked_in=False)
    if len(appts) == 0:
        return False
    contextAppts = []
    for appt in appts:
        contextAppts.append({
            'form': VerifyForm({'appt_id': appt.id}),
            'patient_first_name': appt.patient.first_name,
            'patient_last_name': appt.patient.last_name,
            'picture': appt.patient.image_link,
            'doctor_first_name': appt.doctor.first_name,
            'doctor_last_name': appt.doctor.last_name,
            'scheduled_time': appt.scheduled_time,
            'reason': appt.reason,
        })
    return contextAppts

def create_calendar():
    try:
        Calendar.objects.get(name='Main Calendar')
        return False
    except Calendar.DoesNotExist:
        print('calendar not found')
    print('creating calendar')
    cal = Calendar(name="Main Calendar", slug="main")
    cal.save()
    try:
        rule = Rule.objects.get(name="Daily")
    except Rule.DoesNotExist:
        rule = Rule(frequency="YEARLY", name="Yearly", description="will recur once every Year")
        rule.save()
        rule = Rule(frequency="MONTHLY", name="Monthly", description="will recur once every Month")
        rule.save()
        rule = Rule(frequency="WEEKLY", name="Weekly", description="will recur once every Week")
        rule.save()
        rule = Rule(frequency="DAILY", name="Daily", description="will recur once every Day")
        rule.save()

    return cal

def update_calendar(appt):
    print('updating calendar')
    cal = Calendar.objects.get(name='Main Calendar')
    data = {
            'title': appt['patient'].first_name + ' ' + appt['patient'].last_name,
            'start': appt['scheduled_time'],
            'end': appt['scheduled_time'] + timedelta(minutes=appt['duration']),
            'calendar': cal
    }
    Event.objects.create(**data)
    return True



### Helpers
def timeformater(dt):
    if not dt:
        return None
    p = parser.parse(dt)
    return pytz.timezone(timezone.get_default_timezone_name()).localize(p)


### Decorators
def doctor_required(func):
    def wrapper(request, *args, **kwargs):
        if not Doctor.objects.all().exists():
            #messages.warning(request, "Please Verify New Doctor", extra_tags="info")
            return redirect(reverse('doctor'))
        if 'doctor_secure' not in request.session.keys():
            return redirect(reverse('checkin'))
        return func(request, *args, **kwargs)
    return wrapper

