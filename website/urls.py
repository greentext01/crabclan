from django.urls.conf import path
from . import views


urlpatterns = [
    path('', views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("approve/<int:id>/", views.approve, name="approve"),
    path("admin/", views.admin, name="admin"),
    path("card/", views.idcard, name="card"),
    path("img/", views.card_img, name="img"),
]
