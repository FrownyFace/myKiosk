from __future__ import absolute_import, unicode_literals
from celery import shared_task

from .utils import create_appointments_local, create_patients_local
from .models import Doctor


@shared_task
def task_debug():
    print('DEBUG')
    return 'DEBUG'


@shared_task
def process_webhook(event, body):
    appts_hooks = ['APPOINTMENT_CREATE', 'APPOINTMENT_MODIFY']
    patient_hooks = ['PATIENT_CREATE', 'PATIENT_MODIFY']
    print(event)
    if event in appts_hooks:
        if event == appts_hooks[0]:
            try:
                doctor = Doctor.objects.get(doctor_id=body['doctor'])
                create_appointments_local([body], doctor.doctor_user)
                print('appt added')
                return True
            except Exception as e:
                print(e)
                return False
    elif event in patient_hooks:
        if event == patient_hooks[0]:
            try:
                create_patients_local([body])
                print('patient added')
                return True
            except Exception as e:
                print(e)
                return False
    return True
