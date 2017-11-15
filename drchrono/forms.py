from django import forms
from django.core import validators
from django.forms import extras
from django.core.exceptions import ValidationError
from localflavor.us.us_states import US_STATES
from datetime import datetime

from models import Patient
from api import patch_patient

class NewDoctorForm(forms.Form):
    first_name = forms.CharField(min_length=3, max_length=50, label='First Name',
                                 widget=forms.TextInput(attrs={'required': True, 'class': 'form-control', 'readonly':True}))
    last_name = forms.CharField(max_length=50, label='Last Name',
                                widget=forms.TextInput(attrs={'required': True, 'class': 'form-control', 'readonly':True}))
    office_name = forms.CharField(max_length=100, label='Office Name',
                                   widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}))
    office_phone = forms.CharField(max_length=50, label='Office Phone',
                                widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}))
    kiosk_key = forms.CharField(max_length=50, label='Kiosk Key',
                                widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}))

    doctor_id = forms.CharField(widget=forms.HiddenInput(), max_length=50, required=False)

class CheckInForm(forms.Form):
    first_name = forms.CharField(max_length=50, label='First Name',
                                 widget=forms.TextInput(attrs={'required': True, 'class': 'input-field col s6 form-control'}))
    last_name = forms.CharField(max_length=50, label='Last Name',
                                widget=forms.TextInput(attrs={'required': True, 'class': 'input-field col s6 form-control'}))

    def is_valid(self):
        return super(CheckInForm, self).is_valid()

class VerifyForm(forms.Form):
    ssn = forms.RegexField('^[0-9]{4}', label="Last Four Digits of SSN", required=False,  widget=forms.TextInput(attrs={'class': 'input-field'}))
    appt_id = forms.CharField(widget=forms.HiddenInput(), max_length=50, required=True)

class InfoForm(forms.ModelForm):

    class Meta:
        model = Patient
        fields = '__all__'
        widgets = {
            'dob': extras.SelectDateWidget(years=[1900+i for i in range(100)], attrs={'class': 'browser-default'}),
            'id': forms.HiddenInput(),
            'patient_id': forms.HiddenInput(),
            'ssn': forms.HiddenInput(),
            'image_link': forms.HiddenInput()
            #'state': forms.Select(US_STATES),
        }

    def is_valid(self):
        return super(InfoForm, self).is_valid()

    def patch_and_save(self, request):
        payload = {
            'first_name': self.cleaned_data['first_name'],
            'last_name': self.cleaned_data['last_name'],
            'date_of_birth': self.cleaned_data['dob'].date(),
            'gender': self.cleaned_data['gender'],
            'race': self.cleaned_data['race'],
            'ethnicity': self.cleaned_data['ethnicity'],
            'address': self.cleaned_data['address'],
            'city': self.cleaned_data['city'],
            'zipcode': self.cleaned_data['zipcode'],
            'state': self.cleaned_data['state'],
            'cell_phone': self.cleaned_data['cell_phone'],
            'home_phone': self.cleaned_data['home_phone'],
            'email': self.cleaned_data['email'],
            'emergency_contact_name': self.cleaned_data['emergency_contact_name'],
            'emergency_contact_phone': self.cleaned_data['emergency_contact_phone'],
        }

        response = patch_patient(request, self.cleaned_data['patient_id'], payload)
        print(response)
        if response.status_code < 400:
            return True
        return False
