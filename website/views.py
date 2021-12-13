import base64
import os
import pathlib
import re
import qrcode
import uuid

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import PermissionDenied, ValidationError
from django.http.response import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django_email_verification import send_email
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF

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


@login_required
def admin(request):
    if request.user.job.staff or request.user.is_superuser:
        return render(request, 'admin.html', {
            'users': User.objects.filter(is_active=True)
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
            user = form.save()
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


def random_media(ext):
    return str(uuid.uuid1()) + ext


@login_required
def idcard(request):
    if not request.user.approved:
        return redirect('index')

    url = os.environ.get('URL')

    image = Image.open(settings.ASSET_ROOT / 'background.png').convert('RGBA')
    rank = Image.open(settings.ASSET_ROOT /
                      f'{request.user.job.rank}{request.user.job.type}.png').convert('RGBA')

    image.paste(rank, (522, 101), rank)

    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(str(settings.ASSET_ROOT / 'font.ttf'), 48)

    draw.text((56, 229), request.user.get_full_name(),
              font=font, align="left", fill='black')

    qr = qrcode.QRCode(box_size=4)
    qr.add_data(f'{url}qrinfo/{request.user.uuid}/')
    qr.make()
    qr_img = qr.make_image()

    image.paste(qr_img, (10, image.size[1] - qr_img.size[1] - 10))

    image_relpath = random_media('.png')
    image_path = str(pathlib.Path(settings.MEDIA_ROOT) / image_relpath)

    image.save(image_path)

    ################
    # Generate pdf #
    ################

    pdf_path = str(random_media('.pdf'))

    pdf = FPDF()
    pdf.add_page()
    pdf.image(name=image_path, w=85, h=54, link='', type='')
    pdf.output(dest='F', name=str(
        pathlib.Path(settings.MEDIA_ROOT) / pdf_path))

    # Remove the oldest files if there is more than 5 cards
    media = list(pathlib.Path(settings.MEDIA_ROOT).iterdir())

    if len(media) > 10:
        while len(media) > 10:
            min(media, key=lambda f: f.stat().st_mtime).unlink()
            media = list(pathlib.Path(settings.MEDIA_ROOT).iterdir())

    return render(request, 'card.html', {
        'card': str(image_relpath),
        'pdf': str(pdf_path)
    })


@login_required
def media(request, file):
    if not request.user.approved:
        return redirect('index')
    try:
        return FileResponse(open(os.path.join(settings.MEDIA_ROOT, file), 'rb'))
    except:
        raise Http404()


@login_required
def fire(request, id):
    if request.user.job.is_staff or request.user.is_superuser:
        get_object_or_404(User, pk=id).delete()
        return redirect('admin')
    else:
        raise PermissionDenied()


def qrinfo(request, id):
    user = get_object_or_404(User, uuid=id)
    return render(request, 'qrinfo.html', {
        'qr_user': user
    })
