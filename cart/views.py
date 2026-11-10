import re
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Product

from .cart import Cart


def _parse_quantity(text, allow_zero=False):
    """Return a whole number from 1 to 999 (or 0 if allowed), otherwise None."""
    text = text.strip()
    if not re.fullmatch(r"[0-9]{1,3}", text):
        return None
    quantity = int(text)
    if quantity == 0 and not allow_zero:
        return None
    return quantity


def _get_public_product(product_id):
    return get_object_or_404(
        Product, pk=product_id, is_published=True, shop__is_published=True
    )


def cart_detail(request):
    cart = Cart(request)
    groups = cart.groups()
    for notice in cart.notices:
        messages.warning(request, notice)

    total = sum((group["subtotal"] for group in groups), Decimal("0"))
    return render(request, "cart/cart_detail.html", {"groups": groups, "total": total})


@require_POST
def cart_add(request, product_id):
    product = _get_public_product(product_id)

    quantity = _parse_quantity(request.POST.get("quantity", "1"))
    if quantity is None:
        messages.error(request, "Please enter a valid quantity (a whole number, 1 or more).")
        return redirect("marketplace:product_detail", slug=product.slug)

    if product.stock <= 0:
        messages.error(request, "Sorry, this product is out of stock.")
        return redirect("marketplace:product_detail", slug=product.slug)

    cart = Cart(request)
    wanted = cart.quantity_of(product) + quantity
    saved = cart.add(product, quantity)

    if saved < wanted:
        messages.warning(
            request, f"Only {product.stock} in stock. Your cart now has {saved} of this item."
        )
    else:
        messages.success(request, f"'{product.name}' was added to your cart.")
    return redirect("cart:detail")


@require_POST
def cart_update(request, product_id):
    product = _get_public_product(product_id)

    quantity = _parse_quantity(request.POST.get("quantity", ""), allow_zero=True)
    if quantity is None:
        messages.error(request, "Please enter a valid quantity (0 removes the item).")
        return redirect("cart:detail")

    saved = Cart(request).set_quantity(product, quantity)
    if saved < quantity:
        messages.warning(request, f"Only {product.stock} in stock. Quantity set to {saved}.")
    else:
        messages.success(request, "Your cart was updated.")
    return redirect("cart:detail")


@require_POST
def cart_remove(request, product_id):
    Cart(request).remove(product_id)
    messages.success(request, "The item was removed from your cart.")
    return redirect("cart:detail")