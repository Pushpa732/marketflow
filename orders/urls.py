from django.urls import path

from . import seller_views, views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("my/orders/", views.order_list, name="order_list"),
    path("my/orders/<slug:order_number>/", views.order_detail, name="order_detail"),
    path("seller/orders/", seller_views.seller_order_list, name="seller_order_list"),
    path(
        "seller/orders/<slug:order_number>/",
        seller_views.seller_order_detail,
        name="seller_order_detail",
    ),
    path(
        "seller/orders/<slug:order_number>/action/",
        seller_views.seller_order_action,
        name="seller_order_action",
    ),
]