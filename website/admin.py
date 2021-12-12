from django.contrib import admin

from website.models import Job
from .models import User

# Register your models here.
admin.site.register(User)
admin.site.register(Job)