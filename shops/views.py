from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import seller_required

from .forms import ShopForm
from .models import Shop


@seller_required
def seller_dashboard(request):
    shop = Shop.objects.filter(owner=request.user).first()
    return render(request, "shops/seller_dashboard.html", {"shop": shop})


@seller_required
def shop_profile(request):
    shop = Shop.objects.filter(owner=request.user).first()

    if request.method == "POST":
        form = ShopForm(request.POST, request.FILES, instance=shop)
        if form.is_valid():
            shop = form.save(commit=False)
            shop.owner = request.user
            shop.save()
            messages.success(request, "Your shop profile has been saved.")
            return redirect("shops:seller_dashboard")
    else:
        form = ShopForm(instance=shop)

    return render(request, "shops/shop_form.html", {"form": form, "shop": shop})



@seller_required
@require_POST
def toggle_publish(request):
    shop = get_object_or_404(Shop, owner=request.user)

    if shop.is_published:
        shop.is_published = False
        messages.success(request, "Your shop is now hidden (draft).")
    elif not shop.description.strip():
        messages.error(request, "Please add a shop description before publishing.")
    else:
        shop.is_published = True
        messages.success(request, "Your shop is now published.")

    shop.save()
    return redirect("shops:seller_dashboard")