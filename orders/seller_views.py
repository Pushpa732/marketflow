from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import seller_required
from payments.models import Payment
from shops.models import Shop

from .models import Order

ORDERS_PER_PAGE = 10


def _seller_shop(user):
    return Shop.objects.filter(owner=user).first()


def _query_string(request):
    """Current address parameters without 'page', so paging keeps the filters."""
    params = request.GET.copy()
    params.pop("page", None)
    encoded = params.urlencode()
    return encoded + "&" if encoded else ""


@seller_required
def seller_order_list(request):
    shop = _seller_shop(request.user)
    if shop is None:
        messages.error(request, "Please create your shop before managing orders.")
        return redirect("shops:shop_profile")

    # Only the orders of this seller's own shop.
    orders = shop.orders.select_related("payment").prefetch_related("items")

    status = request.GET.get("status", "")
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    else:
        status = ""

    query = request.GET.get("q", "").strip()[:100]
    if query:
        orders = orders.filter(
            Q(order_number__icontains=query)
            | Q(shipping_name__icontains=query)
            | Q(shipping_phone__icontains=query)
        )

    # Tab counts always describe the whole shop, not the current filter.
    counts = dict(shop.orders.order_by().values_list("status").annotate(total=Count("id")))
    tabs = [{"value": "", "label": "All", "count": sum(counts.values())}]
    for value, label in Order.Status.choices:
        tabs.append({"value": value, "label": label, "count": counts.get(value, 0)})

    for tab in tabs:
        params = {}
        if tab["value"]:
            params["status"] = tab["value"]
        if query:
            params["q"] = query
        encoded = urlencode(params)
        tab["url"] = f"{request.path}?{encoded}" if encoded else request.path

    page_obj = Paginator(orders, ORDERS_PER_PAGE).get_page(request.GET.get("page"))
    context = {
        "shop": shop,
        "page_obj": page_obj,
        "tabs": tabs,
        "active_status": status,
        "query": query,
        "query_string": _query_string(request),
    }
    return render(request, "orders/seller_order_list.html", context)


@seller_required
def seller_order_detail(request, order_number):
    shop = _seller_shop(request.user)
    if shop is None:
        messages.error(request, "Please create your shop before managing orders.")
        return redirect("shops:shop_profile")

    # shop=shop is the privacy rule: orders of other shops give a 404.
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        order_number=order_number,
        shop=shop,
    )
    payment = Payment.objects.filter(order=order).first()
    return render(
        request,
        "orders/seller_order_detail.html",
        {"order": order, "payment": payment},
    )