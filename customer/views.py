
# from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login
# from .forms import SignupForm
# import random
# from django.core.cache import cache
# from django.contrib.auth.models import User

# def signup(request):
#     if request.method == 'POST':
#         form = SignupForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.first_name = form.cleaned_data.get('first_name')
#             # user.last_name = form.cleaned_data.get('last_name')
#             user.phone_number = form.cleaned_data.get('phone_number')
#             user.is_active = False  
#             user.save()
            
#             phone_number = form.cleaned_data.get('phone_number')
#             otp = random.randint(1000, 9999)
#             cache.set(phone_number, otp, timeout=300)  # Cache OTP for 5 mins
            
#             # Call the function to send the OTP here, e.g., send_otp(phone_number, otp)
            
#             return redirect('otp_verify', phone_number=phone_number)
#     else:
#         form = SignupForm()
#     return render(request, 'customer/signup.html', {'form': form})

# # LoginIN

# def login(request):
#     if request.method == 'POST':
#         phone_number = request.POST.get('phone_number')
#         otp = request.POST.get('otp')
#         cached_otp = cache.get(phone_number)
#         if cached_otp == int(otp):
#             user = authenticate(request, phone_number=phone_number)
#             if user is not None:
#                 login(request, user)
#                 return redirect('home')
#         else:
#             # Handle incorrect OTP
#             return render(request, 'customer/login.html', {'error': 'Invalid OTP'})
#     return render(request, 'customer/login.html')


# def verify_otp(request):
#     if request.method == 'POST':
#         phone_number = request.POST.get('phone_number')
#         otp = request.POST.get('otp')
        
#         cached_otp = cache.get(phone_number)
        
#         if cached_otp == int(otp):
#             user = User.objects.get(phone_number=phone_number)
#             user.is_active = True
#             user.save()
#             login(request, user)
#             return redirect('home')
#         else:
#             # Handle incorrect OTP
#             return render(request, 'customer/verify_otp.html', {'error': 'Invalid OTP'})

#     return render(request, 'customer/verify_otp.html')




# # Twilio
# from twilio.rest import Client

# def send_otp(phone_number, otp):
#     account_sid = 'your_account_sid'
#     auth_token = 'your_auth_token'
#     client = Client(account_sid, auth_token)
    
#     message = client.messages.create(
#         body=f'Your OTP is {otp}',
#         from_='+1234567890',  # Your Twilio phone number
#         to=phone_number
#     )


# NEW CODE
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login# resturant/customer/views.py
from .models import User

# ...
from .forms import SignupForm
import random
from django.core.cache import cache
from django.contrib.auth import get_user_model  # Import to get custom user model
from django.http import HttpResponse

# Fetch the custom user model
User = get_user_model()

# Signup View
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Set to False until OTP verification
            user.save()
            
            phone_number = form.cleaned_data.get('phone')
            otp = random.randint(1000, 9999)
            cache.set(phone_number, otp, timeout=300)  # Cache OTP for 5 mins
            
            send_otp(phone_number, otp)  # Function to send OTP
            
            return redirect('verify_otp', phone_number=phone_number)
    else:
        form = SignupForm()
    
    return render(request, 'customer/signup.html', {'form': form})

# Login View
def login(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone')
        password = request.POST.get('password')
        
        user = authenticate(request, username=phone_number, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            return render(request, 'customer/login.html', {'error': 'Invalid credentials'})

    return render(request, 'customer/login.html')

# OTP Verification View
def verify_otp(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone')
        otp = ''.join([request.POST.get(f'otp{i}') for i in range(1, 5)])  # Collecting OTP from inputs
        cached_otp = cache.get(phone_number)
        
        if cached_otp and cached_otp == int(otp):
            user = User.objects.get(phone_number=phone_number)
            user.is_active = True
            user.save()
            auth_login(request, user)
            return redirect('home')
        else:
            return render(request, 'customer/verify_otp.html', {'error': 'Invalid OTP'})

    return render(request, 'customer/verify_otp.html')

# Function to send OTP (Twilio integration)
from twilio.rest import Client

def send_otp(phone_number, otp):
    account_sid = 'your_account_sid'
    auth_token = 'your_auth_token'
    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        body=f'Your OTP is {otp}',
        from_='+1234567890',  # Your Twilio phone number
        to=phone_number
    )


# bot
from django.http import JsonResponse
from .voice_bot import start_bot  # Import your bot function

def activate_voice_bot(request):
    if request.method == "GET" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        start_bot()  # Call the bot activation function
        return JsonResponse({'message': 'Voice bot activated!'})
    return JsonResponse({'message': 'Invalid request'}, status=400)
