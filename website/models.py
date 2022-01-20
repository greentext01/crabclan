from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

# Create your models here.


class Job(models.Model):
    name = models.CharField(max_length=64, unique=True)
    unique = models.BooleanField(default=False)
    staff = models.BooleanField(default=False)

    PEASENT = 0
    SOLDIER = 1
    MINER = 2
    BUILDER = 3
    PRESIDENT = 4
    SPECIAL_OPS = 5
    JOB_TYPE_CHOICES = [
        (PEASENT, 'Peasent'),
        (SOLDIER, 'Soldier'),
        (MINER, 'Miner'),
        (BUILDER, 'Builder'),
        (PRESIDENT, 'President'),
        (SPECIAL_OPS, 'Special ops'),
    ]

    type = models.IntegerField(choices=JOB_TYPE_CHOICES, default=SOLDIER)

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    email = models.EmailField(unique=True)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, related_name="userjob", null=True)
    approved = models.BooleanField(default=False)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
