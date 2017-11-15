from __future__ import absolute_import, unicode_literals
from celery import task

from .models import Appointment, Patient, WebhookTransaction
from .utils import create_appointments_local, create_patients_local


@task()
def task_debug():
    print('DEBUG')
    return 'DEBUG'

@task()
def process_webhook(request, event, body):
    appts_hooks = ['APPOINTMENT_CREATE', 'APPOINTMENT_MODIFY']
    patient_hooks = ['PATIENT_CREATE', 'PATIENT_MODIFY']
    if event in appts_hooks:
        if event == appts_hooks[0]:
            try:
                create_appointments_local([body], request.user)
            except:
                return False
    elif event in patient_hooks:
        if event == patient_hooks[0]:
            try:
                create_patients_local([body])
            except:
                return False
    return True

'''
class ProcessMessages(PeriodicTask):
    run_every = crontab()  # this will run once a minute
    def run(self, **kwargs):
        print('test celery')
        return 'hi mom'

    def get_transactions_to_process(self):
        return WebhookTransaction.objects.filter(
            event_name__in=self.event_names,
            status=WebhookTransaction.UNPROCESSED
        )
    def process_trans(self, trans):
        a = {}
        return Patient.create(**a)

unprocessed_trans = self.get_transactions_to_process()

        for trans in unprocessed_trans:
            try:
                self.process_trans(trans)
                trans.status = WebhookTransaction.PROCESSED
                trans.save()

            except Exception:
                trans.status = WebhookTransaction.ERROR
                trans.save()
                '''