from django.shortcuts import render

from shops.models import Shop


def home(request):
    shops = Shop.objects.filter(is_published=True).order_by("-created_at")
    return render(request, "marketplace/home.html", {"shops": shops})