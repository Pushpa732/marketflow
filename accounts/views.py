from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect("marketplace:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to MarketFlow! Your account has been created.")
            return redirect("marketplace:home")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})