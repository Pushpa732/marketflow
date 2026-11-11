from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path(
        "my/orders/<slug:order_number>/payment/",
        views.submit_transaction_id,
        name="submit_transaction_id",
    ),
]