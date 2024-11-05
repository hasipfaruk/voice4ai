from django.urls import path
from . import views
from . import views


urlpatterns = [
    # path('', views.signup, name='index'),
    path('', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('index/', views.login, name='home'),
]

