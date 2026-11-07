from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import seller_required
from shops.models import Shop

from .forms import ProductForm, ProductImageForm
from .models import Product, ProductImage

MAX_IMAGES_PER_PRODUCT = 5


def _get_shop(user):
    return Shop.objects.filter(owner=user).first()


@seller_required
def product_list(request):
    shop = _get_shop(request.user)
    if shop is None:
        messages.error(request, "Please create your shop before managing products.")
        return redirect("shops:shop_profile")

    products = shop.products.select_related("category").prefetch_related("images")
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


@seller_required
def product_edit(request, pk):
    shop = _get_shop(request.user)
    if shop is None:
        messages.error(request, "Please create your shop before managing products.")
        return redirect("shops:shop_profile")

    product = get_object_or_404(Product, pk=pk, shop=shop)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("catalog:product_list")
    else:
        form = ProductForm(instance=product)

    return render(request, "catalog/product_form.html", {"form": form, "product": product})


@seller_required
def product_delete(request, pk):
    shop = _get_shop(request.user)
    if shop is None:
        messages.error(request, "Please create your shop before managing products.")
        return redirect("shops:shop_profile")

    product = get_object_or_404(Product, pk=pk, shop=shop)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("catalog:product_list")

    return render(request, "catalog/product_confirm_delete.html", {"product": product})


@seller_required
def product_images(request, pk):
    shop = _get_shop(request.user)
    if shop is None:
        messages.error(request, "Please create your shop before managing products.")
        return redirect("shops:shop_profile")

    product = get_object_or_404(Product, pk=pk, shop=shop)

    if request.method == "POST":
        if product.images.count() >= MAX_IMAGES_PER_PRODUCT:
            messages.error(
                request, f"A product can have at most {MAX_IMAGES_PER_PRODUCT} images."
            )
            return redirect("catalog:product_images", pk=product.pk)

        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.product = product
            image.save()
            messages.success(request, "Image uploaded.")
            return redirect("catalog:product_images", pk=product.pk)
    else:
        form = ProductImageForm()

    context = {
        "product": product,
        "images": product.images.all(),
        "form": form,
        "max_images": MAX_IMAGES_PER_PRODUCT,
        "can_upload": product.images.count() < MAX_IMAGES_PER_PRODUCT,
    }
    return render(request, "catalog/product_images.html", context)


@seller_required
@require_POST
def product_image_delete(request, pk, image_pk):
    shop = _get_shop(request.user)
    if shop is None:
        messages.error(request, "Please create your shop before managing products.")
        return redirect("shops:shop_profile")

    image = get_object_or_404(ProductImage, pk=image_pk, product__pk=pk, product__shop=shop)
    image.image.delete(save=False)
    image.delete()
    messages.success(request, "Image deleted.")
    return redirect("catalog:product_images", pk=pk)