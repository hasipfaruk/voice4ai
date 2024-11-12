# # from django.db import models
# # from django.contrib.auth.models import AbstractUser

# # class User(AbstractUser):
# #     phone_number = models.CharField(max_length=15, unique=True)
# #     otp = models.CharField(max_length=6, blank=True, null=True)
# #     is_phone_verified = models.BooleanField(default=False)

# #     def __str__(self):
# #         return self.username
# #     pass


# from django.db import models
# from django.contrib.auth.models import User

# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     phone = models.CharField(max_length=15, blank=True)
    
#     def __str__(self):
#         return self.user.username


# customer/models.py

# from django.contrib.auth.models import AbstractUser
# from django.db import models

# class User(AbstractUser):
#     phone = models.CharField(max_length=15, blank=True, null=True)
#     otp = models.CharField(max_length=6, blank=True, null=True)
#     is_phone_verified = models.BooleanField(default=False)
    
#     def __str__(self):
#         return self.username


# models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("The Phone field must be set")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)

class User(AbstractBaseUser):
    # name = models.CharField(max_length=255)
    
    name = models.CharField(max_length=255, default="Default Name")

    # phone = models.CharField(max_length=15, unique=True)
    
    phone = models.CharField(max_length=15, unique=True, default="0000000000")  # Set a reasonable default value

    is_active = models.BooleanField(default=False)  # For OTP verification
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['name']
