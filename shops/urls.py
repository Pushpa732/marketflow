from django.urls import path

from . import views

app_name = "shops"

urlpatterns = [
    path("dashboard/", views.seller_dashboard, name="seller_dashboard"),
]