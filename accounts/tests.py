from django.test import TestCase
from django.urls import reverse

from .models import User

PASSWORD = "StrongPass#2026"


class RegistrationTests(TestCase):
    def valid_data(self, **changes):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "phone": "01700000000",
            "role": "customer",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(changes)
        return data

    def test_customer_can_register(self):
        response = self.client.post(reverse("accounts:register"), self.valid_data())
        self.assertRedirects(response, reverse("marketplace:home"))
        self.assertEqual(User.objects.get(username="newuser").role, "customer")

    def test_seller_can_register(self):
        self.client.post(reverse("accounts:register"), self.valid_data(role="seller"))
        self.assertEqual(User.objects.get(username="newuser").role, "seller")

    def test_cannot_register_as_admin(self):
        response = self.client.post(reverse("accounts:register"), self.valid_data(role="admin"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_password_mismatch_is_rejected(self):
        response = self.client.post(
            reverse("accounts:register"), self.valid_data(password2="Different#2026")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())


class LoginTests(TestCase):
    def setUp(self):
        User.objects.create_user(username="rahim", password=PASSWORD, role="customer")

    def test_login_with_correct_password(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "rahim", "password": PASSWORD}
        )
        self.assertRedirects(response, reverse("marketplace:home"))

    def test_login_with_wrong_password(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "rahim", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)