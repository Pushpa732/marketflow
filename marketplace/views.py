from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from catalog.models import Product
from shops.models import Shop


def _public_products():
    """Products that customers may see: published product in a published shop."""
    return (
        Product.objects.filter(is_published=True, shop__is_published=True)
        .select_related("shop", "category")
        .prefetch_related("images")
    )


def home(request):
    context = {
        "latest_products": _public_products()[:8],
        "shops": Shop.objects.filter(is_published=True).order_by("-created_at")[:6],
    }
    return render(request, "marketplace/home.html", context)


def product_list(request):
    page_obj = Paginator(_public_products(), 12).get_page(request.GET.get("page"))
    return render(request, "marketplace/product_list.html", {"page_obj": page_obj})


def shop_list(request):
    shops = Shop.objects.filter(is_published=True).order_by("name")
    page_obj = Paginator(shops, 12).get_page(request.GET.get("page"))
    return render(request, "marketplace/shop_list.html", {"page_obj": page_obj})


def shop_detail(request, slug):
    shop = get_object_or_404(Shop, slug=slug, is_published=True)
    products = (
        shop.products.filter(is_published=True)
        .select_related("category", "shop")
        .prefetch_related("images")
    )
    page_obj = Paginator(products, 12).get_page(request.GET.get("page"))
    return render(request, "marketplace/shop_detail.html", {"shop": shop, "page_obj": page_obj})


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("shop", "category").prefetch_related("images"),
        slug=slug,
        is_published=True,
        shop__is_published=True,
    )
    related = (
        Product.objects.filter(shop=product.shop, is_published=True)
        .exclude(pk=product.pk)
        .select_related("shop")
        .prefetch_related("images")[:4]
    )
    return render(
        request,
        "marketplace/product_detail.html",
        {"product": product, "related": related},
    )