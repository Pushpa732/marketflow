from django.db import transaction

from orders.models import Order

from .models import Payment

CLOSED_ORDER_STATUSES = (Order.Status.REJECTED, Order.Status.CANCELLED)

# action name: label, button style, and the status the payment gets
ACTIONS = {
    "paid": {"label": "Mark as paid", "style": "success", "status": Payment.Status.PAID},
    "failed": {"label": "Mark as failed", "style": "outline-danger", "status": Payment.Status.FAILED},
    "refunded": {
        "label": "Mark as refunded",
        "style": "outline-secondary",
        "status": Payment.Status.REFUNDED,
    },
    "reopen": {"label": "Reopen payment", "style": "outline-primary", "status": Payment.Status.PENDING},
}

# Which actions make sense for each current payment status.
ACTIONS_BY_STATUS = {
    Payment.Status.PENDING: ["paid", "failed"],
    Payment.Status.FAILED: ["reopen"],
    Payment.Status.PAID: ["refunded"],
    Payment.Status.REFUNDED: [],
}


class PaymentActionError(Exception):
    """Raised when a payment action is not allowed."""


def check_payment_action(payment, order, action):
    """Return an explanation if the action is not allowed, or None if it is allowed."""
    if action not in ACTIONS:
        return "This action is not available."

    order_is_closed = order.status in CLOSED_ORDER_STATUSES

    if action == "paid":
        if payment.status != Payment.Status.PENDING:
            return "Only a pending payment can be marked as paid."
        if order_is_closed:
            return "This order is rejected or cancelled, so its payment cannot be marked as paid."
        if payment.method == Payment.Method.COD:
            if order.status not in (Order.Status.SHIPPED, Order.Status.COMPLETED):
                return "Cash on delivery can be marked as paid after the order is shipped."
        elif not payment.transaction_id:
            return "The customer has not entered a transaction ID yet."
        return None

    if action == "failed":
        if payment.status != Payment.Status.PENDING:
            return "Only a pending payment can be marked as failed."
        return None

    if action == "refunded":
        if payment.status != Payment.Status.PAID:
            return "Only a paid payment can be refunded."
        return None

    # action == "reopen"
    if payment.status != Payment.Status.FAILED:
        return "Only a failed payment can be reopened."
    if order_is_closed:
        return "This order is rejected or cancelled, so its payment cannot be reopened."
    return None


def available_payment_actions(payment, order):
    """The buttons to show for this payment, with a hint when one is not possible yet."""
    buttons = []
    for action in ACTIONS_BY_STATUS[payment.status]:
        error = check_payment_action(payment, order, action)
        buttons.append(
            {
                "action": action,
                "label": ACTIONS[action]["label"],
                "style": ACTIONS[action]["style"],
                "enabled": error is None,
                "hint": error or "",
            }
        )
    return buttons


def apply_payment_action(order_id, shop, action):
    """Carry out a seller action on the payment of an order of this shop."""
    if action not in ACTIONS:
        raise PaymentActionError("This action is not available.")

    with transaction.atomic():
        # shop=shop makes sure the order belongs to this seller.
        order = Order.objects.select_for_update().filter(pk=order_id, shop=shop).first()
        if order is None:
            raise PaymentActionError("Order not found.")

        payment = Payment.objects.select_for_update().filter(order=order).first()
        if payment is None:
            raise PaymentActionError("This order has no payment record.")

        error = check_payment_action(payment, order, action)
        if error:
            raise PaymentActionError(error)

        payment.status = ACTIONS[action]["status"]
        payment.save(update_fields=["status", "paid_at", "updated_at"])

    return payment