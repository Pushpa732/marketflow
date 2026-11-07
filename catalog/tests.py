import io
import shutil
import tempfile
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import User
from shops.models import Shop

from .forms import ProductImageForm
from .models import Category, Product, ProductImage

PASSWORD = "StrongPass#2026"
TEMP_MEDIA = tempfile.mkdtemp()


def make_image(name="test.png"):
    """Create a small real PNG image in memory."""
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class CatalogTestBase(TestCase):
    def setUp(self):
        self.seller1 = User.objects.create_user(username="seller1", password=PASSWORD, role="seller")
        self.seller2 = User.objects.create_user(username="seller2", password=PASSWORD, role="seller")
        self.customer = User.objects.create_user(username="cust", password=PASSWORD, role="customer")
        self.shop1 = Shop.objects.create(owner=self.seller1, name="Shop One", description="First shop")
        self.shop2 = Shop.objects.create(owner=self.seller2, name="Shop Two", description="Second shop")
        self.category = Category.objects.create(name="Fashion")
        self.product1 = Product.objects.create(
            shop=self.shop1, category=self.category, name="Blue T-Shirt",
            price=Decimal("450.00"), stock=20,
        )
        self.product2 = Product.objects.create(
            shop=self.shop2, name="Red Mug", price=Decimal("150.00"), stock=10,
        )

    def login(self, username):
        self.client.login(username=username, password=PASSWORD)

    def product_data(self, **changes):
        data = {
            "name": "Cotton Panjabi",
            "category": self.category.pk,
            "description": "Soft cotton",
            "price": "1200.00",
            "stock": "3",
            "low_stock_threshold": "5",
        }
        data.update(changes)
        return data


class ModelTests(CatalogTestBase):
    def test_category_slug_is_created(self):
        category = Category.objects.create(name="Home & Living")
        self.assertEqual(category.slug, "home-living")

    def test_duplicate_product_names_get_unique_slugs(self):
        second = Product.objects.create(
            shop=self.shop1, name="Blue T-Shirt", price=Decimal("100.00"), stock=1
        )
        self.assertEqual(self.product1.slug, "blue-t-shirt")
        self.assertEqual(second.slug, "blue-t-shirt-2")

    def test_low_stock_property(self):
        low = Product.objects.create(
            shop=self.shop1, name="Low Item", price=Decimal("10.00"),
            stock=3, low_stock_threshold=5,
        )
        self.assertTrue(low.is_low_stock)
        self.assertFalse(self.product1.is_low_stock)

    def test_price_must_be_positive(self):
        product = Product(shop=self.shop1, name="Free Item", price=Decimal("0"), stock=1)
        with self.assertRaises(ValidationError):
            product.full_clean()


class ProductAccessTests(CatalogTestBase):
    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("catalog:product_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_customer_cannot_open_product_pages(self):
        self.login("cust")
        self.assertEqual(self.client.get(reverse("catalog:product_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("catalog:product_create")).status_code, 403)

    def test_seller_without_shop_is_sent_to_create_shop(self):
        User.objects.create_user(username="newseller", password=PASSWORD, role="seller")
        self.login("newseller")
        response = self.client.get(reverse("catalog:product_list"))
        self.assertRedirects(response, reverse("shops:shop_profile"))


class ProductCrudTests(CatalogTestBase):
    def test_seller_sees_only_own_products(self):
        self.login("seller1")
        response = self.client.get(reverse("catalog:product_list"))
        self.assertContains(response, "Blue T-Shirt")
        self.assertNotContains(response, "Red Mug")

    def test_seller_can_add_product(self):
        self.login("seller1")
        response = self.client.post(reverse("catalog:product_create"), self.product_data())
        self.assertRedirects(response, reverse("catalog:product_list"))
        product = Product.objects.get(name="Cotton Panjabi")
        self.assertEqual(product.shop, self.shop1)

    def test_seller_cannot_choose_the_shop(self):
        self.login("seller1")
        self.client.post(
            reverse("catalog:product_create"), self.product_data(shop=self.shop2.pk)
        )
        self.assertEqual(Product.objects.get(name="Cotton Panjabi").shop, self.shop1)

    def test_zero_price_is_rejected(self):
        self.login("seller1")
        response = self.client.post(
            reverse("catalog:product_create"), self.product_data(price="0")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(name="Cotton Panjabi").exists())

    def test_seller_can_edit_own_product(self):
        self.login("seller1")
        url = reverse("catalog:product_edit", args=[self.product1.pk])
        response = self.client.post(
            url, self.product_data(name="Blue T-Shirt", price="500.00", stock="20")
        )
        self.assertRedirects(response, reverse("catalog:product_list"))
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.price, Decimal("500.00"))

    def test_seller_cannot_edit_another_sellers_product(self):
        self.login("seller1")
        url = reverse("catalog:product_edit", args=[self.product2.pk])
        response = self.client.post(url, self.product_data(price="1.00"))
        self.assertEqual(response.status_code, 404)
        self.product2.refresh_from_db()
        self.assertEqual(self.product2.price, Decimal("150.00"))

    def test_delete_page_does_not_delete_by_itself(self):
        self.login("seller1")
        url = reverse("catalog:product_delete", args=[self.product1.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Product.objects.filter(pk=self.product1.pk).exists())

    def test_seller_can_delete_own_product(self):
        self.login("seller1")
        url = reverse("catalog:product_delete", args=[self.product1.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("catalog:product_list"))
        self.assertFalse(Product.objects.filter(pk=self.product1.pk).exists())

    def test_seller_cannot_delete_another_sellers_product(self):
        self.login("seller1")
        url = reverse("catalog:product_delete", args=[self.product2.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Product.objects.filter(pk=self.product2.pk).exists())


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProductImageTests(CatalogTestBase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def images_url(self, product):
        return reverse("catalog:product_images", args=[product.pk])

    def test_seller_can_upload_valid_image(self):
        self.login("seller1")
        url = self.images_url(self.product1)
        response = self.client.post(url, {"image": make_image()})
        self.assertRedirects(response, url)
        self.assertEqual(self.product1.images.count(), 1)

    def test_non_image_file_is_rejected(self):
        self.login("seller1")
        bad_file = SimpleUploadedFile("note.txt", b"hello", content_type="text/plain")
        response = self.client.post(self.images_url(self.product1), {"image": bad_file})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.product1.images.count(), 0)

    def test_too_large_image_is_rejected(self):
        self.login("seller1")
        with patch.object(ProductImageForm, "MAX_SIZE_MB", 0):
            response = self.client.post(
                self.images_url(self.product1), {"image": make_image()}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.product1.images.count(), 0)

    def test_maximum_of_five_images(self):
        for number in range(5):
            ProductImage.objects.create(
                product=self.product1, image=f"product_images/img{number}.png"
            )
        self.login("seller1")
        self.client.post(self.images_url(self.product1), {"image": make_image()})
        self.assertEqual(self.product1.images.count(), 5)

    def test_seller_cannot_upload_to_another_sellers_product(self):
        self.login("seller1")
        response = self.client.post(self.images_url(self.product2), {"image": make_image()})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.product2.images.count(), 0)

    def test_seller_can_delete_own_image(self):
        self.login("seller1")
        self.client.post(self.images_url(self.product1), {"image": make_image()})
        image = self.product1.images.get()
        url = reverse("catalog:product_image_delete", args=[self.product1.pk, image.pk])
        self.client.post(url)
        self.assertEqual(self.product1.images.count(), 0)

    def test_seller_cannot_delete_another_sellers_image(self):
        image = ProductImage.objects.create(
            product=self.product2, image="product_images/other.png"
        )
        self.login("seller1")
        url = reverse("catalog:product_image_delete", args=[self.product2.pk, image.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)