import csv

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render

from accounts.decorators import seller_required
from shops.models import Shop

from .forms import ProductImportForm
from .importers import ALL_COLUMNS, CSVFormatError, read_csv_rows

PREVIEW_ROWS = 5


@seller_required
def product_import(request):
    shop = Shop.objects.filter(owner=request.user).first()
    if shop is None:
        messages.error(request, "Please create your shop before importing products.")
        return redirect("shops:shop_profile")

    preview = None

    if request.method == "POST":
        form = ProductImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                rows = read_csv_rows(form.cleaned_data["file"])
            except CSVFormatError as error:
                form.add_error("file", str(error))
            else:
                preview = {"total": len(rows), "rows": rows[:PREVIEW_ROWS]}
    else:
        form = ProductImportForm()

    return render(request, "catalog/product_import.html", {"form": form, "preview": preview})


@seller_required
def product_import_template(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="marketflow_product_template.csv"'
    response.write("\ufeff")  # helps Excel read non-English text correctly

    writer = csv.writer(response)
    writer.writerow(ALL_COLUMNS)
    writer.writerow(["Cotton Shirt", "Fashion", "Soft cotton shirt", "850.00", "15", "5", "no"])
    writer.writerow(["Notebook", "Books", "A5 ruled notebook", "120.00", "40", "10", "no"])
    return response