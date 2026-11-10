from django.urls import reverse

from .models import Address
from .tests import AddressTestBase


class NextUrlTests(AddressTestBase):
    def test_safe_next_address_is_followed_after_saving(self):
        self.login()
        url = reverse("customers:address_create") + "?next=/checkout/"
        response = self.client.post(url, self.address_data())
        self.assertRedirects(response, "/checkout/", fetch_redirect_response=False)

    def test_external_next_address_is_ignored(self):
        self.login()
        url = reverse("customers:address_create") + "?next=https://evil.example/"
        response = self.client.post(url, self.address_data())
        self.assertRedirects(response, reverse("customers:address_list"))

    def test_next_address_also_works_when_editing(self):
        self.login()
        address = self.make_address(self.customer)
        url = reverse("customers:address_edit", args=[address.pk]) + "?next=/checkout/"
        response = self.client.post(url, self.address_data(city="Sylhet"))
        self.assertRedirects(response, "/checkout/", fetch_redirect_response=False)
        address.refresh_from_db()
        self.assertEqual(address.city, "Sylhet")