from social.apps.django_app.default.models import UserSocialAuth
from social.apps.django_app.utils import load_strategy
import requests

URL_ROOT = 'https://drchrono.com/api/'


class Endpoint(object):
    def __init__(self, req):
        user = UserSocialAuth.objects.get(user=req.user)
        user.refresh_token(load_strategy(req))

        self.access_token = user.access_token
        self.headers = {'Authorization': 'Bearer %s' % self.access_token}

    def get(self, url, payload=None):
        if not payload:
            payload = {}
        return requests.get(url, headers=self.headers, params=payload).json()

    def post(self, url, payload=None):
        if not payload:
            payload = {}
        return requests.post(url, headers=self.headers, data=payload)

    def patch(self, url, payload=None):
        if not payload:
            payload = {}
        return requests.patch(url, headers=self.headers, data=payload)


### HELPERS
def patch_appointment(request, appointment_id, payload):
    e = Endpoint(request)
    url = "{}/appointments/{}".format(URL_ROOT, appointment_id)
    response = e.patch(url, payload=payload)
    print(response)
    return response
