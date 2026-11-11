from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from accounts.decorators import customer_required
from orders.models import Order

from .forms import TransactionIdForm
from .models import Payment

DUPLICATE_MESSAGE = (
    "This transaction ID has already been used for another order. Please check it and try again."
)


@customer_required
@require_POST
def submit_transaction_id(request, order_number):
    # Only the customer's own orders can be found here.
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    payment = get_object_or_404(Payment, order=order)
    back = redirect("orders:order_detail", order_number=order.order_number)

    if payment.method == Payment.Method.COD:
        messages.error(request, "Cash on delivery orders do not need a transaction ID.")
        return back

    order_is_closed = order.status in (Order.Status.REJECTED, Order.Status.CANCELLED)
    if payment.status != Payment.Status.PENDING or order_is_closed:
        messages.error(request, "The transaction ID can no longer be changed for this order.")
        return back

    form = TransactionIdForm(request.POST)
    if not form.is_valid():
        messages.error(request, form.errors["transaction_id"][0])
        return back

    transaction_id = form.cleaned_data["transaction_id"]

    already_used = (
        Payment.objects.filter(method=payment.method, transaction_id=transaction_id)
        .exclude(pk=payment.pk)
        .exists()
    )
    if already_used:
        messages.error(request, DUPLICATE_MESSAGE)
        return back

    try:
        with transaction.atomic():
            payment.transaction_id = transaction_id
            payment.save(update_fields=["transaction_id", "updated_at"])
    except IntegrityError:
        messages.error(request, DUPLICATE_MESSAGE)
        return back

    messages.success(
        request,
        f"Transaction ID saved. {order.shop.name} will check it and confirm your payment.",
    )
    return back