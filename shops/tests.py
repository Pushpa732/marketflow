from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Shop

PASSWORD = "StrongPass#2026"


class SellerAccessTests(TestCase):
    def setUp(self):
        User.objects.create_user(username="cust", password=PASSWORD, role="customer")
        User.objects.create_user(username="sell", password=PASSWORD, role="seller")

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("shops:seller_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_customer_cannot_open_seller_dashboard(self):
        self.client.login(username="cust", password=PASSWORD)
        response = self.client.get(reverse("shops:seller_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_publish(self):
        self.client.login(username="cust", password=PASSWORD)
        response = self.client.post(reverse("shops:toggle_publish"))
        self.assertEqual(response.status_code, 403)

    def test_seller_can_open_seller_dashboard(self):
        self.client.login(username="sell", password=PASSWORD)
        response = self.client.get(reverse("shops:seller_dashboard"))
        self.assertEqual(response.status_code, 200)


class ShopTests(TestCase):
    def setUp(self):
        self.seller1 = User.objects.create_user(username="seller1", password=PASSWORD, role="seller")
        self.seller2 = User.objects.create_user(username="seller2", password=PASSWORD, role="seller")
        self.shop1 = Shop.objects.create(
            owner=self.seller1, name="Rahim Books", description="Books for everyone"
        )

    def test_seller_can_create_shop(self):
        self.client.login(username="seller2", password=PASSWORD)
        response = self.client.post(
            reverse("shops:shop_profile"),
            {"name": "Karim Store", "description": "Daily needs", "category": "Grocery"},
        )
        self.assertRedirects(response, reverse("shops:seller_dashboard"))
        shop = Shop.objects.get(owner=self.seller2)
        self.assertEqual(shop.name, "Karim Store")
        self.assertEqual(shop.slug, "karim-store")

    def test_dashboard_shows_only_own_shop(self):
        self.client.login(username="seller2", password=PASSWORD)
        response = self.client.get(reverse("shops:seller_dashboard"))
        self.assertIsNone(response.context["shop"])
        self.assertNotContains(response, "Rahim Books")

    def test_seller_cannot_change_another_sellers_shop(self):
        self.client.login(username="seller2", password=PASSWORD)
        self.client.post(
            reverse("shops:shop_profile"),
            {"name": "Karim Store", "description": "Daily needs"},
        )
        self.shop1.refresh_from_db()
        self.assertEqual(self.shop1.name, "Rahim Books")
        self.assertEqual(Shop.objects.count(), 2)

    def test_publish_requires_description(self):
        shop = Shop.objects.create(owner=self.seller2, name="No Description")
        self.client.login(username="seller2", password=PASSWORD)
        self.client.post(reverse("shops:toggle_publish"))
        shop.refresh_from_db()
        self.assertFalse(shop.is_published)

    def test_seller_can_publish_and_unpublish(self):
        self.client.login(username="seller1", password=PASSWORD)
        self.client.post(reverse("shops:toggle_publish"))
        self.shop1.refresh_from_db()
        self.assertTrue(self.shop1.is_published)
        self.client.post(reverse("shops:toggle_publish"))
        self.shop1.refresh_from_db()
        self.assertFalse(self.shop1.is_published)

    def test_publish_rejects_get_request(self):
        self.client.login(username="seller1", password=PASSWORD)
        response = self.client.get(reverse("shops:toggle_publish"))
        self.assertEqual(response.status_code, 405)

    def test_home_shows_only_published_shops(self):
        self.shop1.is_published = True
        self.shop1.save()
        Shop.objects.create(
            owner=self.seller2, name="Hidden Draft", description="Not ready", is_published=False
        )
        response = self.client.get(reverse("marketplace:home"))
        self.assertContains(response, "Rahim Books")
        self.assertNotContains(response, "Hidden Draft")