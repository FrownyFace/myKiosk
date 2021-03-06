from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
import hashlib
import numpy as np
import json, copy
from dateutil.relativedelta import relativedelta
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Spectral6
from django.views.decorators.csrf import csrf_exempt

from tasks import process_webhook, task_debug
from celery import debug_task

from utils import *
from forms import *

def login(request):
    return render(request, 'login.html')

def logout(request):
    return redirect(reverse('login'))

@login_required
def enable_kiosk(request):
    if request.method == 'GET':
        raise Http404("Wrong Method")
    elif request.method == 'POST':
        key = request.POST.get("key", "")
        if key == Doctor.objects.get(doctor_user=request.user).kiosk_key:
            del request.session['doctor_secure']
        else:
            messages.error(request, "Wrong key", extra_tags="danger")
    return redirect(reverse('home'))

@login_required
def disable_kiosk(request):
    if request.method == 'GET':
        raise Http404("Wrong Method")
    elif request.method == 'POST':
        key = request.POST.get("key", "")
        if key == Doctor.objects.get(doctor_user=request.user).kiosk_key:
            request.session['doctor_secure'] = True
        else:
            messages.error(request, "Wrong key", extra_tags="danger")
    return redirect(reverse('home'))

@doctor_required
@login_required
def home(request):
    create_calendar()
    update_local(request)
    #update_calendar(re)
    appts = Appointment.objects.get_appointments()
    avg_waiting_time = Appointment.avg_waiting_time()
    return render(request, 'home.html', {'appointments': appts,
                                         'avg_waiting_time': avg_waiting_time})

@login_required
def doctor(request):
    doc = Doctor.objects.filter(doctor_user=request.user)
    if request.method == 'GET':
        if len(doc) != 0:
            if 'doctor_secure' in request.session.keys():
                doc_info = doc[0]
                doc_form = NewDoctorForm({'first_name': doc_info.first_name,
                                          'last_name': doc_info.last_name,
                                          'office_phone': doc_info.office_phone,
                                          'doctor_id': doc_info.id,
                                          'office_name': doc_info.office_name,
                                          'kiosk_key': doc_info.kiosk_key,
                                          })
            else:
                messages.error(request, "Woah not secure - redirecting", extra_tags="danger")
                return redirect(reverse('home'))
        else:
            doc_info = find_doctor(request)
            doc_form = NewDoctorForm({'first_name': doc_info['first_name'],
                                      'last_name': doc_info['last_name'],
                                      'office_phone': doc_info['office_phone'],
                                      'doctor_id': doc_info['id'],
                                      'office_name': 'Office A',
                                      'kiosk_key': 'disable_kiosk',
                                      })
        return render(request, 'doctor.html', {'form': doc_form})
    elif request.method == 'POST':
        form = NewDoctorForm(request.POST)
        if form.is_valid():
            if len(doc) != 0:
                if 'doctor_secure' in request.session.keys():
                    if update_doctor(request, doc[0], form.cleaned_data):
                        messages.success(request, "Doctor Updated", extra_tags="success")
                    else:
                        messages.error(request, "Doctor could not be updated", extra_tags="danger")
                else:
                    messages.error(request, "Woah not secure - redirecting", extra_tags="danger")
                    return redirect(reverse('home'))
            else:
                if add_doctor(request, form.cleaned_data):
                    request.session['doctor_secure'] = True
                    messages.success(request, "Doctor Added", extra_tags="success")
                else:
                    messages.error(request, "Doctor could not be created", extra_tags="danger")
            return redirect(reverse('home'))
        else:
            messages.error(request, "Form is not valid", extra_tags="danger")
    return redirect(reverse('home'))


@login_required
def checkin(request):
    if request.method == 'GET':
        form = CheckInForm()
        avg_waiting_time = Appointment.avg_waiting_time()
        doctor_secure = True if 'doctor_secure' in request.session else False
        return render(request, 'checkin.html', {'checkinForm': form,
                                                'avg_waiting_time': avg_waiting_time,
                                                'doctor_secure': doctor_secure})
    elif request.method == 'POST':
        form = CheckInForm(request.POST)
        if form.is_valid():
            params = {'first_name': form.cleaned_data['first_name'],
                      'last_name': form.cleaned_data['last_name'],
                      }
            patient = find_patient_local(params)
            if not patient:
                messages.error(request, "Patient Not Found", extra_tags="danger")
                return redirect(reverse('checkin'))
            return redirect('/verify/{}/'.format(patient.id))
        else:
            messages.error(request, "Form is not valid", extra_tags="danger")
    return redirect(reverse('checkin'))

@login_required
def verify(request, patient_id):
    if request.method == 'GET':
        try:
            patient = Patient.objects.get(id=patient_id)
            appts = find_appts_by_patient_local(patient)
            if not appts:
                messages.error(request, "No Appointments Found", extra_tags="danger")
                return redirect(reverse('checkin'))
            return render(request, 'verify.html', {'appts_list': appts, 'patient_id': patient_id})
        except:
            return render(request, '404.html')

    if request.method == 'POST':
        form = VerifyForm(request.POST)
        if form.is_valid():
            try:
                #print(hashlib.sha256(form.cleaned_data['ssn']).hexdigest())
                #print(Patient.objects.get(id=patient_id).ssn)
                if hashlib.sha256(form.cleaned_data['ssn']).hexdigest() == Patient.objects.get(id=patient_id).ssn:
                    request.session['one_time_secure'] = True
                    return redirect('/info/{}/'.format(form.cleaned_data['appt_id']))
            except:
                messages.error(request, "SSN is not valid or you do not exist", extra_tags="danger")
        else:
            messages.error(request, "Form is not valid", extra_tags="danger")

    return redirect(reverse('checkin'))

@login_required
def info(request, appt_id):
    if 'one_time_secure' in request.session.keys() or 'doctor_secure' in request.session.keys():
        if request.method == 'GET':
            try:
                appt = Appointment.objects.get(id=appt_id)
                infoForm = InfoForm(Patient.objects.get(id=appt.patient.id).__dict__)
            except:
                infoForm = InfoForm()
            return render(request, 'info.html', {'infoForm': infoForm})
        elif request.method == 'POST':
            appt = Appointment.objects.get(id=appt_id)
            patient = Patient.objects.get(id=appt.patient.id)

            infoForm = InfoForm(instance=patient, data=request.POST)
            infoForm.id = patient.id
            infoForm.patient_id = patient.patient_id
            if infoForm.is_valid():
                if infoForm.patch_and_save(request) and appt.checked_in_func(request):
                    infoForm.save(commit=True)
                    messages.success(request, "Patient and Appointment saved", extra_tags="success")
                else:
                    messages.error(request, "AHHHH SOMETHING IS WRONG", extra_tags="danger")
            return redirect(reverse('home'))

        del request.session['one_time_secure']
    else:
        messages.error(request, "Woah not secure - redirecting", extra_tags="danger")
    return redirect(reverse('home'))

@doctor_required
@login_required
def see(request, appt_id):
    if request.method == 'GET':
        try:
            appt = Appointment.objects.get(id=appt_id)
            appt.seen_func(request)
            messages.success(request, "Seen", extra_tags="success")
        except:
            messages.error(request, "Seen Failed", extra_tags="danger")
    return redirect(reverse('home'))

@doctor_required
@login_required
def complete(request, appt_id):
    if request.method == 'GET':
        try:
            appt = Appointment.objects.get(id=appt_id)
            appt.completed_func(request)
            messages.success(request, "Complete", extra_tags="success")
        except:
            messages.error(request, "Complete Failed", extra_tags="danger")
    return redirect(reverse('home'))

@doctor_required
@login_required
def schedule(request):
    avg_waiting_time = Appointment.avg_waiting_time()
    return render(request, 'schedule.html', {"avg_waiting_time": avg_waiting_time})

@doctor_required
@login_required
def analysis(request):
    index1 = [
        'blank',
        'indian',
        'asian',
        'black',
        'hawaiian',
        'white',
        'declined',
    ]

    ### RACE
    hover1 = HoverTool(tooltips=[
        ("Race", "@race"),
        ("Count", "@counts"),
    ])

    series1 = [Patient.objects.filter(race=x).count() for x in index1]
    source = ColumnDataSource(data=dict(race=index1, counts=series1, color=Spectral6))
    p1 = figure(x_range=index1, plot_height=475, plot_width=475, title="Race Counts",
               toolbar_location=None, tools=[hover1])
    p1.vbar(x='race', top='counts', width=0.9, color='color', source=source)

    series2 = []
    for x in Patient.objects.values('dob'):
        if x['dob'] is not None:
            series2.append(relativedelta(timezone.now().date(), x['dob'].date()).years)


    ### AGE
    hover2 = HoverTool(tooltips=[
        ("Count", "@top"),
        ("Age Bin", "(@left, @right)")
    ])

    hist, edges = np.histogram(series2, density=False, bins=10)
    p2 = figure(plot_width=475, plot_height=475, background_fill_color="#E8DDCB",
                title="Age Histogram", tools=[hover2])
    p2.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
            fill_color="#036564", line_color="#033649")

    plist = [p1, p2]
    script = []
    div = []
    for p in plist:
        p.toolbar.logo = None
        p.toolbar_location = None
        s, d = components(p, CDN)
        script.append(s)
        div.append(d)

    avg_waiting_time = Appointment.avg_waiting_time()
    return render(request, 'analysis.html',
                  {"the_script": script, "the_div": div,
                  "avg_waiting_time": avg_waiting_time})

@csrf_exempt
def webhook(request):
    if request.method == 'GET':
        return HttpResponse(json.dumps({'secret_token':'haha'}), content_type="application/json", status=200, )
    if request.method == 'POST':
        event = request.META['HTTP_X_DRCHRONO_EVENT']
        body = json.loads(request.body)['object']
        try:
            process_webhook.apply_async(args=[event, body])
        except:
            pass
        return HttpResponse(status=200)
    return HttpResponse(json.dumps({'secret_token': 'haha'}), content_type="application/json", status=200, )

