from django import forms
from django.core import validators
from django.forms import extras
from django.core.exceptions import ValidationError
from localflavor.us.us_states import US_STATES

from models import Patient
#{{ checkinForm.as_p }}
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
        if not all(self.cleaned_data.get(field, None) for field in self.Meta.fields):

            return False

        phone_regex = validators.RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

