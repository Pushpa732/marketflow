from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import Product
from shops.models import Shop

PASSWORD = "StrongPass#2026"


class CartTestBase(TestCase):
    def setUp(self):
        seller1 = User.objects.create_user(username="seller1", password=PASSWORD, role="seller")
        seller2 = User.objects.create_user(username="seller2", password=PASSWORD, role="seller")
        seller3 = User.objects.create_user(username="seller3", password=PASSWORD, role="seller")

        self.shop1 = Shop.objects.create(
            owner=seller1, name="Rahim Fashion", description="Clothes", is_published=True
        )
        self.shop2 = Shop.objects.create(
            owner=seller2, name="Karim Books", description="Books", is_published=True
        )
        self.draft_shop = Shop.objects.create(
            owner=seller3, name="Hidden Store", description="Not ready", is_published=False
        )

        self.shirt = self.make_product(self.shop1, "Blue T-Shirt", "450.00", stock=10)
        self.jacket = self.make_product(self.shop1, "Denim Jacket", "2500.00", stock=3)
        self.novel = self.make_product(self.shop2, "Story Novel", "300.00", stock=5)
        self.draft_product = self.make_product(
            self.shop1, "Secret Draft", "100.00", stock=5, is_published=False
        )
        self.hidden_shop_product = self.make_product(self.draft_shop, "Hidden Item", "100.00", stock=5)
        self.sold_out = self.make_product(self.shop1, "Sold Out Item", "50.00", stock=0)

    def make_product(self, shop, name, price, stock=10, is_published=True):
        return Product.objects.create(
            shop=shop,
            name=name,
            price=Decimal(price),
            stock=stock,
            is_published=is_published,
        )

    def add(self, product, quantity=1, follow=False, **extra):
        data = {"quantity": str(quantity)}
        data.update(extra)
        return self.client.post(reverse("cart:add", args=[product.pk]), data, follow=follow)

    def cart_page(self):
        return self.client.get(reverse("cart:detail"))

    def session_cart(self):
        return self.client.session.get("cart", {})


class AddToCartTests(CartTestBase):
    def test_visitor_can_add_product_without_logging_in(self):
        response = self.add(self.shirt, 2)
        self.assertRedirects(response, reverse("cart:detail"))
        self.assertEqual(self.session_cart(), {str(self.shirt.pk): 2})

    def test_adding_the_same_product_again_increases_quantity(self):
        self.add(self.shirt, 2)
        self.add(self.shirt, 3)
        self.assertEqual(self.session_cart(), {str(self.shirt.pk): 5})

    def test_missing_quantity_defaults_to_one(self):
        self.client.post(reverse("cart:add", args=[self.shirt.pk]))
        self.assertEqual(self.session_cart(), {str(self.shirt.pk): 1})

    def test_quantity_above_stock_is_reduced_with_a_message(self):
        response = self.add(self.jacket, 10, follow=True)
        self.assertEqual(self.session_cart(), {str(self.jacket.pk): 3})
        self.assertContains(response, "Only 3 in stock")

    def test_out_of_stock_product_cannot_be_added(self):
        response = self.add(self.sold_out, 1, follow=True)
        self.assertEqual(self.session_cart(), {})
        self.assertContains(response, "Sorry, this product is out of stock")

    def test_draft_product_cannot_be_added(self):
        response = self.add(self.draft_product)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.session_cart(), {})

    def test_product_of_draft_shop_cannot_be_added(self):
        response = self.add(self.hidden_shop_product)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.session_cart(), {})

    def test_invalid_quantities_are_rejected(self):
        for value in ["abc", "-3", "0", "1.5", "", "1000", "999999"]:
            with self.subTest(quantity=value):
                self.add(self.shirt, value)
                self.assertEqual(self.session_cart(), {})

    def test_adding_requires_a_post_request(self):
        response = self.client.get(reverse("cart:add", args=[self.shirt.pk]))
        self.assertEqual(response.status_code, 405)


class UpdateAndRemoveTests(CartTestBase):
    def update(self, product, quantity):
        return self.client.post(
            reverse("cart:update", args=[product.pk]), {"quantity": str(quantity)}
        )

    def test_quantity_can_be_changed(self):
        self.add(self.shirt, 2)
        self.update(self.shirt, 4)
        self.assertEqual(self.session_cart(), {str(self.shirt.pk): 4})

    def test_quantity_zero_removes_the_item(self):
        self.add(self.shirt, 2)
        self.update(self.shirt, 0)
        self.assertEqual(self.session_cart(), {})

    def test_update_above_stock_is_limited(self):
        self.add(self.jacket, 1)
        self.update(self.jacket, 50)
        self.assertEqual(self.session_cart(), {str(self.jacket.pk): 3})

    def test_invalid_update_keeps_the_old_quantity(self):
        self.add(self.shirt, 2)
        self.update(self.shirt, "abc")
        self.assertEqual(self.session_cart(), {str(self.shirt.pk): 2})

    def test_item_can_be_removed(self):
        self.add(self.shirt, 2)
        self.add(self.novel, 1)
        self.client.post(reverse("cart:remove", args=[self.shirt.pk]))
        self.assertEqual(self.session_cart(), {str(self.novel.pk): 1})

    def test_removing_an_item_that_is_not_in_the_cart_is_harmless(self):
        response = self.client.post(reverse("cart:remove", args=[self.novel.pk]))
        self.assertEqual(response.status_code, 302)

    def test_update_and_remove_require_a_post_request(self):
        self.assertEqual(
            self.client.get(reverse("cart:update", args=[self.shirt.pk])).status_code, 405
        )
        self.assertEqual(
            self.client.get(reverse("cart:remove", args=[self.shirt.pk])).status_code, 405
        )

    def test_draft_product_cannot_be_updated(self):
        response = self.update(self.draft_product, 2)
        self.assertEqual(response.status_code, 404)


class CartPageTests(CartTestBase):
    def test_empty_cart_shows_a_message(self):
        self.assertContains(self.cart_page(), "Your cart is empty")

    def test_cart_page_shows_item_and_correct_total(self):
        self.add(self.shirt, 2)
        response = self.cart_page()
        self.assertContains(response, "Blue T-Shirt")
        self.assertEqual(response.context["total"], Decimal("900.00"))

    def test_items_are_grouped_by_shop_with_subtotals(self):
        self.add(self.shirt, 1)
        self.add(self.novel, 2)
        response = self.cart_page()
        subtotals = {
            group["shop"].name: group["subtotal"] for group in response.context["groups"]
        }
        self.assertEqual(
            subtotals,
            {"Rahim Fashion": Decimal("450.00"), "Karim Books": Decimal("600.00")},
        )
        self.assertEqual(response.context["total"], Decimal("1050.00"))

    def test_price_sent_by_the_browser_is_ignored(self):
        self.add(self.shirt, 1, price="1")
        self.assertEqual(self.cart_page().context["total"], Decimal("450.00"))

    def test_price_change_by_the_seller_is_reflected(self):
        self.add(self.shirt, 1)
        self.shirt.price = Decimal("500.00")
        self.shirt.save()
        self.assertEqual(self.cart_page().context["total"], Decimal("500.00"))

    def test_unpublished_product_is_removed_with_a_notice(self):
        self.add(self.shirt, 1)
        self.add(self.novel, 1)
        self.shirt.is_published = False
        self.shirt.save()
        response = self.cart_page()
        self.assertContains(response, "no longer available")
        self.assertEqual(self.session_cart(), {str(self.novel.pk): 1})

    def test_product_of_unpublished_shop_is_removed(self):
        self.add(self.novel, 1)
        self.shop2.is_published = False
        self.shop2.save()
        response = self.cart_page()
        self.assertContains(response, "no longer available")
        self.assertEqual(self.session_cart(), {})

    def test_stock_drop_reduces_the_quantity(self):
        self.add(self.jacket, 3)
        Product.objects.filter(pk=self.jacket.pk).update(stock=1)
        response = self.cart_page()
        self.assertContains(response, "Only 1 of")
        self.assertEqual(self.session_cart(), {str(self.jacket.pk): 1})

    def test_product_that_sells_out_is_removed(self):
        self.add(self.shirt, 2)
        Product.objects.filter(pk=self.shirt.pk).update(stock=0)
        response = self.cart_page()
        self.assertContains(response, "is out of stock and was removed")
        self.assertEqual(self.session_cart(), {})

    def test_navbar_count_shows_total_quantity(self):
        self.add(self.shirt, 2)
        self.add(self.novel, 1)
        response = self.client.get(reverse("marketplace:home"))
        self.assertEqual(response.context["cart_count"], 3)

    def test_cart_survives_login(self):
        User.objects.create_user(username="cust", password=PASSWORD, role="customer")
        self.add(self.shirt, 2)
        self.client.post(reverse("accounts:login"), {"username": "cust", "password": PASSWORD})
        self.assertEqual(self.session_cart(), {str(self.shirt.pk): 2})

    def test_one_visitor_cannot_see_another_visitors_cart(self):
        self.add(self.shirt, 2)
        other_visitor = Client()
        response = other_visitor.get(reverse("cart:detail"))
        self.assertContains(response, "Your cart is empty")