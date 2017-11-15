from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^enable_kiosk/$', views.enable_kiosk, name='enable_kiosk'),
    url(r'^disable_kiosk/$', views.disable_kiosk, name='disable_kiosk'),
    url(r'^checkin/$', views.checkin, name='checkin'),
    url(r'^verify/(\d+)/$', views.verify, name='verify'),
    url(r'^info/(\d+)/$', views.info, name='info'),
    url(r'^analysis/$', views.analysis, name='analysis'),
    url(r'^schedule/', include('schedule.urls'), name='scheduler'),
    url(r'^schedulez/$', views.schedule, name='schedulez'),
    url(r'^doctor/$', views.doctor, name='doctor'),
    url(r'^see/(\d+)/$', views.see, name='see'),
    url(r'^complete/(\d+)/$', views.complete, name='complete'),

    url(r'^oauth/', include('social.apps.django_app.urls', namespace='social')),
    url(r'^admin/', admin.site.urls),
]
