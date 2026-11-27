from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from accounts.decorators import seller_required
from orders.models import Order
from shops.models import Shop

from .services import PaymentActionError, apply_payment_action

SUCCESS_MESSAGES = {
    "paid": "Payment marked as paid.",
    "failed": "Payment marked as failed.",
    "refunded": "Payment marked as refunded.",
    "reopen": "Payment reopened. The customer can now enter a corrected transaction ID.",
}


@seller_required
@require_POST
def seller_payment_action(request, order_number):
    shop = Shop.objects.filter(owner=request.user).first()
    if shop is None:
        messages.error(request, "Please create your shop before managing orders.")
        return redirect("shops:shop_profile")

    # Only the orders of this seller's own shop can be found here.
    order = get_object_or_404(Order, order_number=order_number, shop=shop)
    action = request.POST.get("action", "")

    try:
        apply_payment_action(order.pk, shop, action)
    except PaymentActionError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, SUCCESS_MESSAGES[action])

    return redirect("orders:seller_order_detail", order_number=order.order_number)