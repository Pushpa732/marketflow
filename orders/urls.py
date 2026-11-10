from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("my/orders/", views.order_list, name="order_list"),
    path("my/orders/<slug:order_number>/", views.order_detail, name="order_detail"),
]