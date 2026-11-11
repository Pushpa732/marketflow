from decimal import Decimal

from django.db import transaction

from catalog.models import Product
from payments.models import Payment
from shops.models import Shop

from .models import Order, OrderItem


class OrderPlacementError(Exception):
    """Raised when the cart cannot be turned into orders."""


def place_orders(*, customer, address, groups, expected_total, payment_method):
    """Turn the cart groups into one Order (with one Payment) per shop. All saved, or none.

    groups          the cart grouped by shop (from Cart.groups())
    expected_total  the grand total the customer saw on the checkout page
    payment_method  "cod", "bkash", or "nagad"
    """
    if not groups:
        raise OrderPlacementError("Your cart is empty.")

    if payment_method not in Payment.Method.values:
        raise OrderPlacementError("Please choose a valid payment method.")

    with transaction.atomic():
        wanted = {}
        for group in groups:
            for line in group["lines"]:
                wanted[line["product"].pk] = line["quantity"]

        # Lock the products so nobody else can change them while we work.
        products = {
            product.pk: product
            for product in Product.objects.select_for_update(of=("self",))
            .filter(pk__in=list(wanted), is_published=True, shop__is_published=True)
            .order_by("pk")
        }
        shops = {
            shop.pk: shop
            for shop in Shop.objects.filter(
                pk__in=[group["shop"].pk for group in groups], is_published=True
            )
        }

        for product_id, quantity in wanted.items():
            product = products.get(product_id)
            if product is None or product.stock < quantity:
                raise OrderPlacementError(
                    "An item in your cart is no longer available in the quantity you chose. "
                    "Please review your cart."
                )

        orders = []
        grand_total = Decimal("0")

        for group in groups:
            shop = shops.get(group["shop"].pk)
            if shop is None:
                raise OrderPlacementError(
                    "A shop in your cart is no longer available. Please review your cart."
                )
            if not shop.accepts_payment_method(payment_method):
                method_name = Payment.Method(payment_method).label
                raise OrderPlacementError(
                    f"{shop.name} does not accept {method_name}. Please choose another payment method."
                )

            lines = [
                (products[line["product"].pk], line["quantity"]) for line in group["lines"]
            ]
            subtotal = sum((product.price * quantity for product, quantity in lines), Decimal("0"))
            delivery_charge = shop.delivery_charge

            order = Order.objects.create(
                customer=customer,
                shop=shop,
                subtotal=subtotal,
                delivery_charge=delivery_charge,
                total=subtotal + delivery_charge,
                shipping_name=address.full_name,
                shipping_phone=address.phone,
                shipping_address=address.address_line,
                shipping_city=address.city,
            )
            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        product=product,
                        product_name=product.name,
                        unit_price=product.price,
                        quantity=quantity,
                    )
                    for product, quantity in lines
                ]
            )
            Payment.objects.create(order=order, method=payment_method, amount=order.total)

            orders.append(order)
            grand_total += order.total

        # Safety check: the customer must get exactly the total they agreed to.
        if expected_total is None or grand_total != expected_total:
            raise OrderPlacementError(
                "Prices or delivery charges changed while you were checking out. "
                "Please review the new total and try again."
            )

    return orders