import csv

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render

from accounts.decorators import seller_required
from shops.models import Shop

from .forms import ProductImportForm
from .importers import ALL_COLUMNS, CSVFormatError, import_products, read_csv_rows

MAX_ERRORS_SHOWN = 50


@seller_required
def product_import(request):
    shop = Shop.objects.filter(owner=request.user).first()
    if shop is None:
        messages.error(request, "Please create your shop before importing products.")
        return redirect("shops:shop_profile")

    import_errors = None
    error_total = 0

    if request.method == "POST":
        form = ProductImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                rows = read_csv_rows(form.cleaned_data["file"])
            except CSVFormatError as error:
                form.add_error("file", str(error))
            else:
                count, errors = import_products(shop, rows)
                if errors:
                    error_total = len(errors)
                    import_errors = errors[:MAX_ERRORS_SHOWN]
                else:
                    label = "product" if count == 1 else "products"
                    messages.success(
                        request,
                        f"{count} {label} imported. Products not marked as published are saved as drafts.",
                    )
                    return redirect("catalog:product_list")
    else:
        form = ProductImportForm()

    context = {
        "form": form,
        "import_errors": import_errors,
        "error_total": error_total,
        "hidden_errors": error_total - len(import_errors) if import_errors else 0,
    }
    return render(request, "catalog/product_import.html", context)


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