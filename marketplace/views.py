from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from catalog.models import Category, Product
from shops.models import Shop

MAX_SEARCH_TERMS = 5


def _public_products():
    """Products that customers may see: published product in a published shop."""
    return (
        Product.objects.filter(is_published=True, shop__is_published=True)
        .select_related("shop", "category")
        .prefetch_related("images")
    )


def _query_string(request):
    """Current address parameters without 'page', so pagination keeps the search."""
    params = request.GET.copy()
    params.pop("page", None)
    encoded = params.urlencode()
    return encoded + "&" if encoded else ""


def home(request):
    context = {
        "latest_products": _public_products()[:8],
        "shops": Shop.objects.filter(is_published=True).order_by("-created_at")[:6],
    }
    return render(request, "marketplace/home.html", context)


def product_list(request):
    products = _public_products()

    category = None
    category_slug = request.GET.get("category", "").strip()
    if category_slug:
        category = Category.objects.filter(slug=category_slug).first()
        if category is None:
            products = products.none()
        else:
            products = products.filter(Q(category=category) | Q(category__parent=category))

    page_obj = Paginator(products, 12).get_page(request.GET.get("page"))
    context = {
        "page_obj": page_obj,
        "category": category,
        "query_string": _query_string(request),
    }
    return render(request, "marketplace/product_list.html", context)


def shop_list(request):
    shops = Shop.objects.filter(is_published=True).order_by("name")
    page_obj = Paginator(shops, 12).get_page(request.GET.get("page"))
    return render(request, "marketplace/shop_list.html", {"page_obj": page_obj})


def search(request):
    query = request.GET.get("q", "").strip()[:100]
    terms = query.split()[:MAX_SEARCH_TERMS]

    products = _public_products().none()
    shops = Shop.objects.none()
    categories = Category.objects.none()

    if terms:
        products = _public_products()
        shops = Shop.objects.filter(is_published=True)
        categories = Category.objects.all()

        for term in terms:
            products = products.filter(
                Q(name__icontains=term)
                | Q(description__icontains=term)
                | Q(category__name__icontains=term)
                | Q(shop__name__icontains=term)
            )
            shops = shops.filter(
                Q(name__icontains=term)
                | Q(description__icontains=term)
                | Q(category__icontains=term)
            )
            categories = categories.filter(name__icontains=term)

        categories = categories.filter(
            products__is_published=True, products__shop__is_published=True
        ).distinct()

    page_obj = Paginator(products, 12).get_page(request.GET.get("page"))
    context = {
        "query": query,
        "page_obj": page_obj,
        "total_products": page_obj.paginator.count,
        "shops": shops.order_by("name")[:6],
        "categories": categories[:8],
        "query_string": _query_string(request),
    }
    return render(request, "marketplace/search_results.html", context)


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