import csv
import io

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