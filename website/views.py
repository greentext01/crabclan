from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.db import IntegrityError
from django import forms
from .models import Job, User

# Create your views here.


def index(request):
    return render(request, 'index.html', {
        'members': User.objects.filter(groups__name='Approved')
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, password)
            job = Job.objects.get(request.POST['job'])
            if job.unique and User.objects.filter(job=job).exists():
                return render(request, "register.html", {
                    "message": "Someone already has that job."
                })

            user.save()
        except IntegrityError:
            return render(request, "register.html", {
                "message": "Username already taken."
            })
        except Job.DoesNotExist:
            return render(request, "register.html", {
                "message": "Please select a job."
            })

        login(request, user)
        return HttpResponseRedirect(reverse('apply') if request.GET.get('apply') == 'true' else reverse('index'))
    else:
        jobs = []
        for job in Job.objects.all():
            if not job.unique and User.objects.filter(job=job).exists():
                    return render(request, "register.html", {
                        "message": "Someone already has that job."
                    })

        return render(request, "register.html", {
            'jobs': jobs
        })


def apply(request):
    if request.user.is_authenticated:
        return render(request, 'apply.html')
    else:
        response = redirect('register')
        response['Location'] += '?apply=true'
        return response
