from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from accounts.decorators import seller_required
from shops.models import Shop

from .forms import ProductForm


def _get_shop(user):
    return Shop.objects.filter(owner=user).first()


@seller_required
def product_list(request):
    shop = _get_shop(request.user)
    if shop is None:
        messages.error(request, "Please create your shop before managing products.")
        return redirect("shops:shop_profile")

    products = shop.products.select_related("category")
    page_obj = Paginator(products, 10).get_page(request.GET.get("page"))
    return render(request, "catalog/product_list.html", {"shop": shop, "page_obj": page_obj})


@seller_required
def product_create(request):
    shop = _get_shop(request.user)
    if shop is None:
        messages.error(request, "Please create your shop before adding products.")
        return redirect("shops:shop_profile")

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.shop = shop
            product.save()
            messages.success(request, "Product added.")
            return redirect("catalog:product_list")
    else:
        form = ProductForm()

    return render(request, "catalog/product_form.html", {"form": form})