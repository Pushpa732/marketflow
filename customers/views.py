from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import customer_required

from .forms import AddressForm
from .models import MAX_ADDRESSES_PER_USER, Address


@customer_required
def address_list(request):
    context = {
        "addresses": request.user.addresses.all(),
        "max_addresses": MAX_ADDRESSES_PER_USER,
    }
    return render(request, "customers/address_list.html", context)


@customer_required
def address_create(request):
    if request.user.addresses.count() >= MAX_ADDRESSES_PER_USER:
        messages.error(
            request,
            f"You can save up to {MAX_ADDRESSES_PER_USER} addresses. Delete one to add another.",
        )
        return redirect("customers:address_list")

    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address saved.")
            return redirect("customers:address_list")
    else:
        form = AddressForm(
            initial={
                "full_name": request.user.get_full_name() or request.user.username,
                "phone": request.user.phone,
            }
        )

    return render(request, "customers/address_form.html", {"form": form})


@customer_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)

    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated.")
            return redirect("customers:address_list")
    else:
        form = AddressForm(instance=address)

    return render(request, "customers/address_form.html", {"form": form, "address": address})


@customer_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)

    if request.method == "POST":
        was_default = address.is_default
        address.delete()
        if was_default:
            replacement = request.user.addresses.first()
            if replacement:
                replacement.is_default = True
                replacement.save()
        messages.success(request, "Address deleted.")
        return redirect("customers:address_list")

    return render(request, "customers/address_confirm_delete.html", {"address": address})


@customer_required
@require_POST
def address_set_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, "Default address changed.")
    return redirect("customers:address_list")