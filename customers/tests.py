from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Address

PASSWORD = "StrongPass#2026"


class AddressTestBase(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="cust", password=PASSWORD, role="customer")
        self.other = User.objects.create_user(username="other", password=PASSWORD, role="customer")
        self.seller = User.objects.create_user(username="seller", password=PASSWORD, role="seller")

    def login(self, username="cust"):
        self.client.login(username=username, password=PASSWORD)

    def address_data(self, **changes):
        data = {
            "full_name": "Rahim Uddin",
            "phone": "01712345678",
            "address_line": "House 12, Road 5",
            "city": "Dhaka",
        }
        data.update(changes)
        return data

    def make_address(self, user, **changes):
        return Address.objects.create(user=user, **self.address_data(**changes))


class AccessTests(AddressTestBase):
    def test_visitor_is_sent_to_login(self):
        response = self.client.get(reverse("customers:address_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_seller_cannot_open_address_pages(self):
        self.login("seller")
        self.assertEqual(self.client.get(reverse("customers:address_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("customers:address_create")).status_code, 403)

    def test_customer_can_open_address_pages(self):
        self.login()
        self.assertEqual(self.client.get(reverse("customers:address_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("customers:address_create")).status_code, 200)


class CreateAddressTests(AddressTestBase):
    def test_customer_can_add_an_address(self):
        self.login()
        response = self.client.post(reverse("customers:address_create"), self.address_data())
        self.assertRedirects(response, reverse("customers:address_list"))
        self.assertEqual(Address.objects.get().user, self.customer)

    def test_first_address_becomes_default_and_second_does_not(self):
        self.login()
        url = reverse("customers:address_create")
        self.client.post(url, self.address_data(full_name="First"))
        self.client.post(url, self.address_data(full_name="Second"))
        self.assertTrue(Address.objects.get(full_name="First").is_default)
        self.assertFalse(Address.objects.get(full_name="Second").is_default)

    def test_choosing_a_new_default_switches_the_old_one_off(self):
        self.login()
        url = reverse("customers:address_create")
        self.client.post(url, self.address_data(full_name="First"))
        self.client.post(url, self.address_data(full_name="Second", is_default="on"))
        self.assertFalse(Address.objects.get(full_name="First").is_default)
        self.assertTrue(Address.objects.get(full_name="Second").is_default)

    def test_customer_cannot_choose_the_owner(self):
        self.login()
        self.client.post(
            reverse("customers:address_create"), self.address_data(user=self.other.pk)
        )
        self.assertEqual(Address.objects.get().user, self.customer)

    def test_valid_phone_formats_are_accepted(self):
        self.login()
        for phone in ["01712345678", "+8801712345678", "8801712345678"]:
            with self.subTest(phone=phone):
                Address.objects.all().delete()
                self.client.post(reverse("customers:address_create"), self.address_data(phone=phone))
                self.assertEqual(Address.objects.count(), 1)

    def test_spaces_and_hyphens_in_phone_are_removed(self):
        self.login()
        self.client.post(
            reverse("customers:address_create"), self.address_data(phone="017-1234 5678")
        )
        self.assertEqual(Address.objects.get().phone, "01712345678")

    def test_invalid_phone_numbers_are_rejected(self):
        self.login()
        for phone in ["abc", "123", "0171234567", "01212345678", "017123456789"]:
            with self.subTest(phone=phone):
                response = self.client.post(
                    reverse("customers:address_create"), self.address_data(phone=phone)
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Address.objects.count(), 0)

    def test_required_fields_are_checked(self):
        self.login()
        for field in ["full_name", "phone", "address_line", "city"]:
            with self.subTest(field=field):
                response = self.client.post(
                    reverse("customers:address_create"), self.address_data(**{field: ""})
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Address.objects.count(), 0)

    def test_no_more_than_five_addresses(self):
        self.login()
        for number in range(5):
            self.make_address(self.customer, full_name=f"Person {number}")
        self.client.post(reverse("customers:address_create"), self.address_data())
        self.assertEqual(Address.objects.filter(user=self.customer).count(), 5)


class EditAndDeleteTests(AddressTestBase):
    def test_customer_can_edit_own_address(self):
        self.login()
        address = self.make_address(self.customer)
        url = reverse("customers:address_edit", args=[address.pk])
        self.client.post(url, self.address_data(city="Chattogram"))
        address.refresh_from_db()
        self.assertEqual(address.city, "Chattogram")

    def test_unticking_the_only_default_keeps_it_default(self):
        self.login()
        address = self.make_address(self.customer)
        self.client.post(reverse("customers:address_edit", args=[address.pk]), self.address_data())
        address.refresh_from_db()
        self.assertTrue(address.is_default)

    def test_customer_cannot_edit_another_customers_address(self):
        self.login()
        address = self.make_address(self.other)
        url = reverse("customers:address_edit", args=[address.pk])
        response = self.client.post(url, self.address_data(city="Hacked"))
        self.assertEqual(response.status_code, 404)
        address.refresh_from_db()
        self.assertEqual(address.city, "Dhaka")

    def test_delete_page_does_not_delete_by_itself(self):
        self.login()
        address = self.make_address(self.customer)
        response = self.client.get(reverse("customers:address_delete", args=[address.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Address.objects.filter(pk=address.pk).exists())

    def test_customer_can_delete_own_address(self):
        self.login()
        address = self.make_address(self.customer)
        self.client.post(reverse("customers:address_delete", args=[address.pk]))
        self.assertFalse(Address.objects.filter(pk=address.pk).exists())

    def test_customer_cannot_delete_another_customers_address(self):
        self.login()
        address = self.make_address(self.other)
        response = self.client.post(reverse("customers:address_delete", args=[address.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Address.objects.filter(pk=address.pk).exists())

    def test_deleting_the_default_promotes_another_address(self):
        self.login()
        first = self.make_address(self.customer, full_name="First")
        second = self.make_address(self.customer, full_name="Second")
        self.client.post(reverse("customers:address_delete", args=[first.pk]))
        second.refresh_from_db()
        self.assertTrue(second.is_default)

    def test_customer_can_change_the_default(self):
        self.login()
        first = self.make_address(self.customer, full_name="First")
        second = self.make_address(self.customer, full_name="Second")
        self.client.post(reverse("customers:address_default", args=[second.pk]))
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)

    def test_customer_cannot_change_another_customers_default(self):
        self.login()
        address = self.make_address(self.other)
        response = self.client.post(reverse("customers:address_default", args=[address.pk]))
        self.assertEqual(response.status_code, 404)

    def test_default_change_requires_a_post_request(self):
        self.login()
        address = self.make_address(self.customer)
        response = self.client.get(reverse("customers:address_default", args=[address.pk]))
        self.assertEqual(response.status_code, 405)


class PrivacyTests(AddressTestBase):
    def test_list_shows_only_own_addresses(self):
        self.make_address(self.customer, full_name="My Home")
        self.make_address(self.other, full_name="Secret Person")
        self.login()
        response = self.client.get(reverse("customers:address_list"))
        self.assertContains(response, "My Home")
        self.assertNotContains(response, "Secret Person")