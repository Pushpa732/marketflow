from django.urls import path

from . import seller_views, views

app_name = "payments"

urlpatterns = [
    path(
        "my/orders/<slug:order_number>/payment/",
        views.submit_transaction_id,
        name="submit_transaction_id",
    ),
    path(
        "seller/orders/<slug:order_number>/payment/",
        seller_views.seller_payment_action,
        name="seller_payment_action",
    ),
]