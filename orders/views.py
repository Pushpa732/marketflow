from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from cart.cart import Cart, summarize


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