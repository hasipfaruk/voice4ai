# from django.urls import path
# from . import views



# urlpatterns = [
#     # path('', views.signup, name='index'),
#     path('', views.login, name='login'),
#     path('signup/', views.signup, name='signup'),
#     path('verify-otp/', views.verify_otp, name='verify_otp'),
#     path('index/', views.login, name='home'),
# ]

# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.signup, name='signup'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login, name='login'),
    # Add other URL paths as needed
    path('index/', views.login, name='home'),

]
