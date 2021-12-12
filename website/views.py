import base64
import pathlib
import re
import uuid
from functools import wraps

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.http.response import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django_email_verification import send_email
from PIL import Image, ImageDraw, ImageFont

from .models import Job, User

# Create your views here.


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        max_length=200, help_text='Enter your school email address', label='School email')
    job = forms.ModelChoiceField(Job.objects.exclude(
        unique=True, userjob__job__isnull=False))

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = User
        fields = ('email', 'username', 'password1',
                  'password2', 'first_name', 'last_name', 'job')

    def clean_email(self):
        email_re = r'\b[A-Za-z0-9._%+-]+@claudel\.org\b'
        email = self.cleaned_data.get("email")

        if not re.fullmatch(email_re, email, re.IGNORECASE):
            raise ValidationError('Enter your school email.')

        if User.objects.filter(email=email).exists():
            raise ValidationError('Email already in use.')

        return email


def index(request):
    return render(request, 'index.html', {
        'members': User.objects.filter(approved=True)
    })


def admin(request):
    if request.user.job.staff or request.user.is_superuser:
        return render(request, 'admin.html', {
            'users': User.objects.filter(approved=False, is_active=True)
        })
    else:
        return redirect('index')


@require_POST
def approve(request, id):
    if request.user.job.staff or request.user.is_superuser:
        user = get_object_or_404(User, pk=id)
        user.approved = True
        user.save()
        return redirect('admin')
    else:
        return redirect('index')


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

        # Attempt to create new user
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            send_email(user)
            return render(request, "email_acc.html")
        else:
            return render(request, "register.html", {
                'form': form
            })

    else:
        return render(request, "register.html", {
            'form': SignupForm(),
        })


@require_GET
def card_img(request):
    return FileResponse(open(base64.b64decode(request.GET.get('card')).decode('ascii'), 'rb'))


@login_required
def idcard(request):
    if not request.user.approved:
        return redirect('index')

    image = Image.open(settings.ASSET_ROOT / 'background.png').convert('RGBA')
    rank = Image.open(settings.ASSET_ROOT /
                      f'{request.user.job.rank}{request.user.job.type}.png').convert('RGBA')

    image.paste(rank, (522, 101), rank)

    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(str(settings.ASSET_ROOT / 'font.ttf'), 48)

    draw.text((56, 229), request.user.get_full_name(), font=font, align="left", fill='black')

    image_name = str(uuid.uuid1()) + '.png'
    image.save(pathlib.Path(settings.MEDIA_ROOT) / image_name)

    # Remove the oldest file if there is more than 5 cards
    images = list(pathlib.Path(settings.MEDIA_ROOT).glob('*.png'))
    if len(images) > 5:
        min(images, key=lambda f: f.stat().st_mtime).unlink()

    return render(request, 'card.html', {
        'card': image_name
    })
