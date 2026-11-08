import csv
import io
import re
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import Category, Product

REQUIRED_COLUMNS = ["name", "price", "stock"]
ALL_COLUMNS = [
    "name",
    "category",
    "description",
    "price",
    "stock",
    "low_stock_threshold",
    "is_published",
]
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB
MAX_ROWS = 500
MAX_PRICE = Decimal("99999999.99")
MAX_NUMBER = 1_000_000
DEFAULT_LOW_STOCK = 5
TRUE_VALUES = {"yes", "y", "true", "1"}
FALSE_VALUES = {"no", "n", "false", "0", ""}


class CSVFormatError(Exception):
    """Raised when the uploaded file as a whole cannot be used."""


def read_csv_rows(uploaded_file):
    """Read an uploaded CSV file and return a list of (row_number, row_dict)."""
    if not uploaded_file.name.lower().endswith(".csv"):
        raise CSVFormatError("Please upload a file with the .csv extension.")

    if uploaded_file.size > MAX_FILE_SIZE:
        raise CSVFormatError("The file is too large. The maximum size is 1 MB.")

    try:
        text = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise CSVFormatError("The file must be saved as a UTF-8 CSV file.")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise CSVFormatError("The file is empty.")

    headers = [name.strip().lower() for name in reader.fieldnames]
    missing = [column for column in REQUIRED_COLUMNS if column not in headers]
    if missing:
        raise CSVFormatError("Missing required column(s): " + ", ".join(missing) + ".")

    rows = []
    for row_number, raw_row in enumerate(reader, start=2):
        row = {}
        for key, value in raw_row.items():
            if key is None:
                continue
            row[key.strip().lower()] = (value or "").strip()

        if not any(row.values()):
            continue  # skip completely blank lines

        rows.append((row_number, row))
        if len(rows) > MAX_ROWS:
            raise CSVFormatError(
                f"The file has more than {MAX_ROWS} rows. Please split it into smaller files."
            )

    if not rows:
        raise CSVFormatError("The file has a header but no product rows.")

    return rows


def _parse_price(text):
    if not text:
        return None, "price is required."
    try:
        price = Decimal(text)
    except InvalidOperation:
        return None, "price must be a number such as 450 or 450.50."
    if not price.is_finite() or price <= 0:
        return None, "price must be greater than 0."
    if price.as_tuple().exponent < -2:
        return None, "price can have at most 2 decimal places."
    if price > MAX_PRICE:
        return None, "price is too large."
    return price, None


def _parse_whole_number(text, field, required, default=None):
    if text == "":
        if required:
            return None, f"{field} is required."
        return default, None
    if not re.fullmatch(r"[0-9]+", text):
        return None, f"{field} must be a whole number such as 10 (no decimals or negative numbers)."
    value = int(text)
    if value > MAX_NUMBER:
        return None, f"{field} is too large."
    return value, None


def _parse_yes_no(text):
    lowered = text.lower()
    if lowered in TRUE_VALUES:
        return True, None
    if lowered in FALSE_VALUES:
        return False, None
    return None, "is_published must be yes or no."


def _validate_row(row, categories):
    """Check one row. Returns (cleaned_data, list_of_error_messages)."""
    errors = []

    name = row.get("name", "")
    if not name:
        errors.append("name is required.")
    elif len(name) > 150:
        errors.append("name must be 150 characters or fewer.")

    price, error = _parse_price(row.get("price", ""))
    if error:
        errors.append(error)

    stock, error = _parse_whole_number(row.get("stock", ""), "stock", required=True)
    if error:
        errors.append(error)

    threshold, error = _parse_whole_number(
        row.get("low_stock_threshold", ""),
        "low_stock_threshold",
        required=False,
        default=DEFAULT_LOW_STOCK,
    )
    if error:
        errors.append(error)

    is_published, error = _parse_yes_no(row.get("is_published", ""))
    if error:
        errors.append(error)

    category = None
    category_name = row.get("category", "")
    if category_name:
        category = categories.get(category_name.lower())
        if category is None:
            errors.append(
                f"category '{category_name}' does not exist. Ask the administrator to add it."
            )

    data = {
        "name": name,
        "category": category,
        "description": row.get("description", ""),
        "price": price,
        "stock": stock,
        "low_stock_threshold": threshold,
        "is_published": is_published,
    }
    return data, errors


def validate_rows(rows, shop):
    """Check every row. Returns (valid_rows, errors)."""
    categories = {}
    for category in Category.objects.all():
        categories.setdefault(category.name.lower(), category)

    existing_names = {name.lower() for name in shop.products.values_list("name", flat=True)}
    seen_names = {}

    valid_rows = []
    errors = []

    for row_number, row in rows:
        data, row_errors = _validate_row(row, categories)

        name_key = data["name"].lower()
        if name_key:
            if name_key in existing_names:
                row_errors.append("a product with this name already exists in your shop.")
            elif name_key in seen_names:
                row_errors.append(f"this name is repeated from row {seen_names[name_key]}.")
            else:
                seen_names[name_key] = row_number

        if row_errors:
            errors.append((row_number, row_errors))
        else:
            valid_rows.append((row_number, data))

    return valid_rows, errors


def import_products(shop, rows):
    """Validate all rows, then save them all or nothing. Returns (count, errors)."""
    valid_rows, errors = validate_rows(rows, shop)
    if errors:
        return 0, errors

    with transaction.atomic():
        for _, data in valid_rows:
            Product.objects.create(shop=shop, **data)

    return len(valid_rows), []