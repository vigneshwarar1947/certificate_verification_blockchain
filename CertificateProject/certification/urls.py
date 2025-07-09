# certification/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Institute login
    path('institute/login/', views.institute_login, name='institute_login'),

    # Certificate submission (requires login)
    path('certificate/submit/', views.submit_certificate, name='submit_certificate'),

    # Verifier page to verify a certificate
    path('certificate/verify/', views.verify_certificate, name='verify_certificate'),
    path('institute/logout/', views.institute_logout, name='institute_logout'),
    path('certificate/success/', views.certificate_success, name='certificate_success'),
    path('certificate/verified/', views.certificate_verified, name='certificate_verified'),



]
