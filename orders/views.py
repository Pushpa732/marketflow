from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import customer_required
from cart.cart import Cart, summarize

from .models import Order
from .services import OrderPlacementError, place_orders


def _parse_money(text):
    try:
        value = Decimal(text or "")
    except InvalidOperation:
        return None
    return value if value.is_finite() else None


def _place_order(request, cart, groups, addresses):
    if cart.notices:
        messages.error(
            request,
            "Your cart changed, so nothing was ordered. Please review it and try again.",
        )
        return redirect("orders:checkout")

    # Only the customer's own addresses are in this list, so another
    # customer's address number can never match.
    chosen = request.POST.get("address", "")
    address = next((a for a in addresses if str(a.pk) == chosen), None)
    if address is None:
        messages.error(request, "Please choose a delivery address.")
        return redirect("orders:checkout")

    try:
        orders = place_orders(
            customer=request.user,
            address=address,
            groups=groups,
            expected_total=_parse_money(request.POST.get("expected_total")),
        )
    except OrderPlacementError as error:
        messages.error(request, str(error))
        return redirect("orders:checkout")

    cart.clear()
    label = "order" if len(orders) == 1 else "orders"
    messages.success(
        request,
        f"Thank you! {len(orders)} {label} placed. The sellers will confirm your {label} soon.",
    )
    return redirect("orders:order_list")


@login_required
def checkout(request):
    if not request.user.is_customer:
        messages.error(request, "Please log in with a customer account to place orders.")
        return redirect("cart:detail")

    cart = Cart(request)
    groups = cart.groups()
    for notice in cart.notices:
        messages.warning(request, notice)

    if not groups:
        messages.info(request, "Your cart is empty.")
        return redirect("cart:detail")

    addresses = list(request.user.addresses.all())

    if request.method == "POST":
        return _place_order(request, cart, groups, addresses)

    requested = request.GET.get("address", "")
    selected = next((a for a in addresses if str(a.pk) == requested), None)
    if selected is None:
        selected = next((a for a in addresses if a.is_default), None)

    context = {
        "groups": groups,
        "summary": summarize(groups),
        "addresses": addresses,
        "selected_address_id": selected.pk if selected else None,
    }
    return render(request, "orders/checkout.html", context)


@customer_required
def order_list(request):
    orders = request.user.orders.select_related("shop").prefetch_related("items")
    page_obj = Paginator(orders, 10).get_page(request.GET.get("page"))
    return render(request, "orders/order_list.html", {"page_obj": page_obj})


@customer_required
def order_detail(request, order_number):
    order = get_object_or_404(
        Order.objects.select_related("shop").prefetch_related("items"),
        order_number=order_number,
        customer=request.user,
    )
    return render(request, "orders/order_detail.html", {"order": order})