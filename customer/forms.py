from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import User

class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=True)  # Adjust max_length as needed

    class Meta:
        model = User
        # fields = ['first_name', 'last_name', 'phone_number', 'username', 'password1', 'password2']
        fields = ('username', 'phone', 'password1', 'password2') 