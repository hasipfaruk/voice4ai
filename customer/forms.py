# from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
# from .models import User

# class SignupForm(UserCreationForm):
#     first_name = forms.CharField(max_length=30, required=True)
#     last_name = forms.CharField(max_length=30, required=True)
#     phone_number = forms.CharField(max_length=15, required=True)  # Adjust max_length as needed

#     class Meta:
#         model = User
#         # fields = ['first_name', 'last_name', 'phone_number', 'username', 'password1', 'password2']
#         fields = ('username', 'phone', 'password1', 'password2') 



# from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from .models import User

# class SignupForm(UserCreationForm):
#     phone = forms.CharField(max_length=15)

#     class Meta:
#         model = User
#         fields = ['username', 'email', 'phone', 'password1', 'password2']



# forms.py
# forms.py
from django import forms
from .models import User

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['name', 'phone', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")
        return cleaned_data
