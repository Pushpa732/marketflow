from django.shortcuts import render

from accounts.decorators import seller_required


@seller_required
def seller_dashboard(request):
    return render(request, "shops/seller_dashboard.html")