from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class Job(models.Model):
    name = models.CharField(max_length=64, unique=True)
    unique = models.BooleanField(default=False)

class User(AbstractUser):
    job = models.ForeignKey(Job, on_delete=models.PROTECT, null=True)
    requested_job = models.ForeignKey(Job, on_delete=models.PROTECT, null=True, related_name='requested')
    email_verified = models.BooleanField(default=False)