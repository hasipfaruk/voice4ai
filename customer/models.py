# from django.db import models
# from django.contrib.auth.models import AbstractUser

# class User(AbstractUser):
#     phone_number = models.CharField(max_length=15, unique=True)
#     otp = models.CharField(max_length=6, blank=True, null=True)
#     is_phone_verified = models.BooleanField(default=False)

#     def __str__(self):
#         return self.username
#     pass


from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return self.user.username