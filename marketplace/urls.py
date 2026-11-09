from django.urls import path

from . import views

app_name = "marketplace"

urlpatterns = [
    path("", views.home, name="home"),
    path("shops/<slug:slug>/", views.shop_detail, name="shop_detail"),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
]