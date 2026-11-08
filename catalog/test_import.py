from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from shops.models import Shop

from .importers import CSVFormatError, import_products, read_csv_rows, validate_rows
from .models import Category, Product

PASSWORD = "StrongPass#2026"
HEADER = "name,category,description,price,stock,low_stock_threshold,is_published\n"


def csv_file(content, name="products.csv"):
    data = content if isinstance(content, bytes) else content.encode("utf-8")
    return SimpleUploadedFile(name, data, content_type="text/csv")


class ImportTestBase(TestCase):
    def setUp(self):
        self.seller1 = User.objects.create_user(username="seller1", password=PASSWORD, role="seller")
        self.seller2 = User.objects.create_user(username="seller2", password=PASSWORD, role="seller")
        self.customer = User.objects.create_user(username="cust", password=PASSWORD, role="customer")
        self.shop1 = Shop.objects.create(owner=self.seller1, name="Shop One", description="First shop")
        self.shop2 = Shop.objects.create(owner=self.seller2, name="Shop Two", description="Second shop")
        self.fashion = Category.objects.create(name="Fashion")

    def login(self, username):
        self.client.login(username=username, password=PASSWORD)

    def check(self, *lines, shop=None):
        """Build a CSV from the given lines and run validation on it."""
        rows = read_csv_rows(csv_file(HEADER + "\n".join(lines) + "\n"))
        return validate_rows(rows, shop or self.shop1)


class ReadCsvFileTests(ImportTestBase):
    def test_valid_file_is_read(self):
        rows = read_csv_rows(csv_file(HEADER + "Shirt,Fashion,Nice,450,10,5,no\n"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], 2)  # row 1 is the header
        self.assertEqual(rows[0][1]["name"], "Shirt")

    def test_wrong_extension_is_rejected(self):
        with self.assertRaises(CSVFormatError):
            read_csv_rows(csv_file(HEADER, name="products.txt"))

    def test_missing_required_column_is_rejected(self):
        with self.assertRaises(CSVFormatError) as context:
            read_csv_rows(csv_file("name,stock\nShirt,5\n"))
        self.assertIn("price", str(context.exception))

    def test_empty_file_is_rejected(self):
        with self.assertRaises(CSVFormatError):
            read_csv_rows(csv_file(""))

    def test_header_without_rows_is_rejected(self):
        with self.assertRaises(CSVFormatError):
            read_csv_rows(csv_file(HEADER))

    def test_blank_lines_are_skipped(self):
        rows = read_csv_rows(csv_file(HEADER + "\n\nShirt,,,450,10,,\n"))
        self.assertEqual(len(rows), 1)

    def test_too_many_rows_are_rejected(self):
        lines = "".join(f"Item{number},,,10,1,,\n" for number in range(501))
        with self.assertRaises(CSVFormatError):
            read_csv_rows(csv_file(HEADER + lines))

    def test_file_over_one_megabyte_is_rejected(self):
        with self.assertRaises(CSVFormatError):
            read_csv_rows(csv_file(b"a" * (1024 * 1024 + 1)))

    def test_file_that_is_not_utf8_is_rejected(self):
        with self.assertRaises(CSVFormatError):
            read_csv_rows(csv_file(b"name,price,stock\n\xff\xfe\n"))

    def test_excel_utf8_marker_is_accepted(self):
        rows = read_csv_rows(csv_file("\ufeff" + HEADER + "Shirt,,,450,10,,\n"))
        self.assertEqual(len(rows), 1)


class RowValidationTests(ImportTestBase):
    def test_valid_row_passes(self):
        valid, errors = self.check("Shirt,Fashion,Nice,450.50,10,5,yes")
        self.assertEqual(errors, [])
        data = valid[0][1]
        self.assertEqual(data["price"], Decimal("450.50"))
        self.assertEqual(data["category"], self.fashion)
        self.assertTrue(data["is_published"])

    def test_optional_columns_get_defaults(self):
        valid, errors = self.check("Mug,,,100,3,,")
        self.assertEqual(errors, [])
        data = valid[0][1]
        self.assertEqual(data["low_stock_threshold"], 5)
        self.assertFalse(data["is_published"])
        self.assertIsNone(data["category"])

    def test_name_is_required(self):
        _, errors = self.check(",Fashion,x,100,5,5,no")
        self.assertIn("name is required.", errors[0][1])

    def test_invalid_prices_are_rejected(self):
        for price in ["abc", "0", "-5", "12.345", ""]:
            with self.subTest(price=price):
                _, errors = self.check(f"Shirt,Fashion,x,{price},5,5,no")
                self.assertEqual(len(errors), 1)

    def test_invalid_stock_is_rejected(self):
        for stock in ["-3", "2.5", "ten", ""]:
            with self.subTest(stock=stock):
                _, errors = self.check(f"Shirt,Fashion,x,100,{stock},5,no")
                self.assertEqual(len(errors), 1)

    def test_unknown_category_is_rejected(self):
        _, errors = self.check("Shirt,Nowhere,x,100,5,5,no")
        self.assertIn("Nowhere", errors[0][1][0])

    def test_category_match_ignores_capital_letters(self):
        _, errors = self.check("Shirt,fashion,x,100,5,5,no")
        self.assertEqual(errors, [])

    def test_invalid_yes_no_is_rejected(self):
        _, errors = self.check("Shirt,Fashion,x,100,5,5,maybe")
        self.assertIn("is_published must be yes or no.", errors[0][1])

    def test_repeated_name_inside_file_is_rejected(self):
        valid, errors = self.check(
            "Shirt,Fashion,x,100,5,5,no",
            "Shirt,Fashion,x,100,5,5,no",
        )
        self.assertEqual(len(valid), 1)
        self.assertEqual(errors[0][0], 3)
        self.assertIn("repeated from row 2", errors[0][1][0])

    def test_name_already_in_own_shop_is_rejected(self):
        Product.objects.create(shop=self.shop1, name="Shirt", price=Decimal("10.00"), stock=1)
        _, errors = self.check("shirt,Fashion,x,100,5,5,no")
        self.assertIn("already exists", errors[0][1][0])

    def test_same_name_in_another_shop_is_allowed(self):
        Product.objects.create(shop=self.shop2, name="Shirt", price=Decimal("10.00"), stock=1)
        _, errors = self.check("Shirt,Fashion,x,100,5,5,no")
        self.assertEqual(errors, [])

    def test_all_problems_in_a_row_are_reported(self):
        _, errors = self.check("Bad,Nowhere,x,abc,-1,5,maybe")
        self.assertEqual(len(errors[0][1]), 4)


class ImportProductsTests(ImportTestBase):
    def rows(self, *lines):
        return read_csv_rows(csv_file(HEADER + "\n".join(lines) + "\n"))

    def test_valid_rows_are_saved_to_the_shop(self):
        count, errors = import_products(
            self.shop1,
            self.rows("Shirt,Fashion,x,100,5,5,no", "Mug,,x,50,8,,no"),
        )
        self.assertEqual(count, 2)
        self.assertEqual(errors, [])
        self.assertEqual(self.shop1.products.count(), 2)
        self.assertEqual(self.shop1.products.get(name="Shirt").slug, "shirt")

    def test_one_bad_row_means_nothing_is_saved(self):
        count, errors = import_products(
            self.shop1,
            self.rows("Good Item,Fashion,x,100,5,5,no", ",Fashion,x,100,5,5,no"),
        )
        self.assertEqual(count, 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(Product.objects.count(), 0)

    def test_published_column_is_respected(self):
        import_products(self.shop1, self.rows("Shirt,Fashion,x,100,5,5,yes"))
        self.assertTrue(self.shop1.products.get(name="Shirt").is_published)


class ImportViewTests(ImportTestBase):
    def setUp(self):
        super().setUp()
        self.url = reverse("catalog:product_import")

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_customer_cannot_open_import_page(self):
        self.login("cust")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_seller_can_open_import_page(self):
        self.login("seller1")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_seller_without_shop_is_sent_to_create_shop(self):
        User.objects.create_user(username="newseller", password=PASSWORD, role="seller")
        self.login("newseller")
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("shops:shop_profile"))

    def test_template_can_be_downloaded(self):
        self.login("seller1")
        response = self.client.get(reverse("catalog:product_import_template"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])
        text = response.content.decode("utf-8-sig")
        self.assertTrue(text.startswith("name,category,description,price,stock"))

    def test_valid_upload_creates_products_in_own_shop(self):
        self.login("seller1")
        response = self.client.post(
            self.url, {"file": csv_file(HEADER + "Shirt,Fashion,x,100,5,5,no\n")}
        )
        self.assertRedirects(response, reverse("catalog:product_list"))
        self.assertEqual(Product.objects.get(name="Shirt").shop, self.shop1)

    def test_bad_upload_shows_report_and_saves_nothing(self):
        self.login("seller1")
        response = self.client.post(
            self.url, {"file": csv_file(HEADER + ",Fashion,x,100,5,5,no\n")}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nothing was imported.")
        self.assertEqual(Product.objects.count(), 0)

    def test_non_csv_upload_shows_error(self):
        self.login("seller1")
        response = self.client.post(self.url, {"file": csv_file("hello", name="notes.txt")})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please upload a file with the .csv extension.")

    def test_each_seller_imports_into_own_shop_only(self):
        self.login("seller2")
        self.client.post(self.url, {"file": csv_file(HEADER + "Shirt,Fashion,x,100,5,5,no\n")})
        self.assertEqual(Product.objects.get(name="Shirt").shop, self.shop2)
        self.assertEqual(self.shop1.products.count(), 0)

    def test_file_cannot_choose_another_shop(self):
        self.login("seller1")
        content = f"name,price,stock,shop\nShirt,100,5,{self.shop2.pk}\n"
        self.client.post(self.url, {"file": csv_file(content)})
        self.assertEqual(Product.objects.get(name="Shirt").shop, self.shop1)