from django.db import transaction
from django.db.models import F

from catalog.models import Product

from .models import Order


class OrderTransitionError(Exception):
    """Raised when an order action is not allowed or cannot be completed."""


# action name: (status the order must have now, status it gets)
SELLER_ACTIONS = {
    "confirm": (Order.Status.PENDING, Order.Status.CONFIRMED),
    "reject": (Order.Status.PENDING, Order.Status.REJECTED),
    "process": (Order.Status.CONFIRMED, Order.Status.PROCESSING),
    "ship": (Order.Status.PROCESSING, Order.Status.SHIPPED),
    "complete": (Order.Status.SHIPPED, Order.Status.COMPLETED),
}


def _deduct_stock(order):
    """Check the stock of every item and reduce it. Raises an error if anything is short."""
    needed = {}
    for item in order.items.select_related("product"):
        if item.product is None or item.product.shop_id != order.shop_id:
            raise OrderTransitionError(
                f"'{item.product_name}' no longer exists in your shop, so this order "
                "cannot be confirmed. You can reject it."
            )
        needed[item.product_id] = needed.get(item.product_id, 0) + item.quantity

    # Lock the products (in a fixed order) so nobody else changes the stock meanwhile.
    products = {
        product.pk: product
        for product in Product.objects.select_for_update(of=("self",))
        .filter(pk__in=list(needed))
        .order_by("pk")
    }

    shortages = []
    for product_id, quantity in needed.items():
        product = products[product_id]
        if product.stock < quantity:
            shortages.append(
                f"{product.name} (ordered {quantity}, in stock {product.stock})"
            )
    if shortages:
        raise OrderTransitionError(
            "Not enough stock for: " + "; ".join(shortages)
            + ". Update your stock or reject the order."
        )

    for product_id, quantity in needed.items():
        Product.objects.filter(pk=product_id).update(stock=F("stock") - quantity)


def apply_seller_action(order_id, shop, action):
    """Carry out a seller action on an order of this shop. Returns the updated order."""
    if action not in SELLER_ACTIONS:
        raise OrderTransitionError("This action is not available.")

    required_status, new_status = SELLER_ACTIONS[action]

    with transaction.atomic():
        # Lock the order row. shop=shop makes sure it belongs to this seller.
        order = Order.objects.select_for_update().filter(pk=order_id, shop=shop).first()
        if order is None:
            raise OrderTransitionError("Order not found.")

        if order.status != required_status:
            raise OrderTransitionError(
                f"This action is not possible because the order is {order.get_status_display().lower()}."
            )

        if action == "confirm":
            _deduct_stock(order)

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

    return order