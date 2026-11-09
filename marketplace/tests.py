from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import Category, Product
from shops.models import Shop

PASSWORD = "StrongPass#2026"


class MarketplaceTestBase(TestCase):
    """Creates a small marketplace: 2 public shops, 1 draft shop, and several products."""

    def setUp(self):
        seller1 = User.objects.create_user(username="seller1", password=PASSWORD, role="seller")
        seller2 = User.objects.create_user(username="seller2", password=PASSWORD, role="seller")
        seller3 = User.objects.create_user(username="seller3", password=PASSWORD, role="seller")

        self.shop1 = Shop.objects.create(
            owner=seller1, name="Rahim Fashion", description="Clothes and more", is_published=True
        )
        self.shop2 = Shop.objects.create(
            owner=seller2, name="Karim Books", description="Books and stationery", is_published=True
        )
        self.draft_shop = Shop.objects.create(
            owner=seller3, name="Hidden Store", description="Not ready", is_published=False
        )

        self.fashion = Category.objects.create(name="Fashion")
        self.books = Category.objects.create(name="Books")

        self.shirt = self.make_product(self.shop1, "Blue T-Shirt", "450.00", self.fashion)
        self.jacket = self.make_product(
            self.shop1, "Denim Jacket", "2500.00", self.fashion, description="Warm winter jacket"
        )
        self.novel = self.make_product(self.shop2, "Story Novel", "300.00", self.books)
        self.draft_product = self.make_product(
            self.shop1, "Secret Draft", "100.00", is_published=False
        )
        self.hidden_shop_product = self.make_product(self.draft_shop, "Hidden Store Item", "100.00")

    def make_product(self, shop, name, price, category=None, is_published=True, description=""):
        return Product.objects.create(
            shop=shop,
            category=category,
            name=name,
            description=description,
            price=Decimal(price),
            stock=10,
            is_published=is_published,
        )

    def add_extra_products(self, count=13):
        for number in range(count):
            self.make_product(self.shop2, f"Extra Item {number}", "100.00")

    def names(self, response):
        return [product.name for product in response.context["page_obj"]]


class VisibilityTests(MarketplaceTestBase):
    def test_anonymous_visitor_can_browse_public_pages(self):
        urls = [
            reverse("marketplace:home"),
            reverse("marketplace:product_list"),
            reverse("marketplace:shop_list"),
            reverse("marketplace:search"),
            reverse("marketplace:shop_detail", args=[self.shop1.slug]),
            reverse("marketplace:product_detail", args=[self.shirt.slug]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_home_shows_only_public_products_and_shops(self):
        response = self.client.get(reverse("marketplace:home"))
        self.assertContains(response, "Blue T-Shirt")
        self.assertContains(response, "Rahim Fashion")
        self.assertNotContains(response, "Secret Draft")
        self.assertNotContains(response, "Hidden Store")

    def test_listing_hides_draft_product_and_products_of_draft_shop(self):
        response = self.client.get(reverse("marketplace:product_list"))
        self.assertContains(response, "Blue T-Shirt")
        self.assertNotContains(response, "Secret Draft")
        self.assertNotContains(response, "Hidden Store Item")

    def test_shop_list_hides_draft_shop(self):
        response = self.client.get(reverse("marketplace:shop_list"))
        self.assertContains(response, "Karim Books")
        self.assertNotContains(response, "Hidden Store")

    def test_draft_product_page_is_not_found(self):
        url = reverse("marketplace:product_detail", args=[self.draft_product.slug])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_product_of_draft_shop_is_not_found(self):
        url = reverse("marketplace:product_detail", args=[self.hidden_shop_product.slug])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_draft_shop_page_is_not_found(self):
        url = reverse("marketplace:shop_detail", args=[self.draft_shop.slug])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_shop_page_lists_only_published_products(self):
        response = self.client.get(reverse("marketplace:shop_detail", args=[self.shop1.slug]))
        self.assertContains(response, "Blue T-Shirt")
        self.assertNotContains(response, "Secret Draft")

    def test_product_page_shows_details_and_related_products(self):
        response = self.client.get(reverse("marketplace:product_detail", args=[self.shirt.slug]))
        self.assertContains(response, "Blue T-Shirt")
        self.assertContains(response, "450.00")
        self.assertContains(response, "Rahim Fashion")
        self.assertContains(response, "Denim Jacket")  # related product from the same shop
        self.assertNotContains(response, "Secret Draft")

    def test_friendly_404_page_is_used(self):
        response = self.client.get("/products/no-such-product/")
        self.assertContains(response, "could not find that page", status_code=404)


class ListingTests(MarketplaceTestBase):
    def test_listing_is_paginated(self):
        self.add_extra_products(13)  # 3 existing public products + 13 = 16
        url = reverse("marketplace:product_list")
        page1 = self.client.get(url)
        page2 = self.client.get(url, {"page": 2})
        self.assertEqual(len(page1.context["page_obj"]), 12)
        self.assertEqual(len(page2.context["page_obj"]), 4)

    def test_page_number_out_of_range_does_not_crash(self):
        response = self.client.get(reverse("marketplace:product_list"), {"page": 999})
        self.assertEqual(response.status_code, 200)

    def test_pagination_links_keep_the_sort_choice(self):
        self.add_extra_products(13)
        response = self.client.get(reverse("marketplace:product_list"), {"sort": "price_low"})
        self.assertContains(response, "sort=price_low&amp;page=2")


class SearchTests(MarketplaceTestBase):
    def search(self, query, **extra):
        params = {"q": query}
        params.update(extra)
        return self.client.get(reverse("marketplace:search"), params)

    def test_search_by_product_name_ignores_capital_letters(self):
        response = self.search("SHIRT")
        self.assertContains(response, "Blue T-Shirt")

    def test_search_with_several_words_needs_all_of_them(self):
        self.assertContains(self.search("blue shirt"), "Blue T-Shirt")
        self.assertNotContains(self.search("blue novel"), "Blue T-Shirt")

    def test_search_by_description(self):
        self.assertContains(self.search("winter"), "Denim Jacket")

    def test_search_by_shop_name_finds_shop_and_its_products(self):
        response = self.search("Karim")
        self.assertContains(response, "Karim Books")
        self.assertContains(response, "Story Novel")

    def test_search_by_category_name_shows_category_link(self):
        response = self.search("Books")
        self.assertContains(response, "Story Novel")
        self.assertContains(response, "?category=books")

    def test_category_without_public_products_is_not_suggested(self):
        Category.objects.create(name="Empty Category")
        response = self.search("Empty")
        self.assertContains(response, "No results")

    def test_draft_product_is_never_found(self):
        response = self.search("Secret")
        self.assertNotContains(response, "Secret Draft")
        self.assertContains(response, "No results")

    def test_product_of_draft_shop_is_never_found(self):
        response = self.search("Hidden")
        self.assertNotContains(response, "Hidden Store")
        self.assertContains(response, "No results")

    def test_search_without_results_shows_friendly_message(self):
        self.assertContains(self.search("zzzz"), "No results")

    def test_empty_search_asks_for_a_word(self):
        response = self.search("")
        self.assertContains(response, "Type a product, shop, or category name")

    def test_script_in_search_text_is_escaped(self):
        response = self.search("<script>alert(1)</script>")
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_sql_like_text_is_harmless(self):
        response = self.search("' OR 1=1 --")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Blue T-Shirt")

    def test_very_long_search_does_not_crash(self):
        response = self.search("a " * 300)
        self.assertEqual(response.status_code, 200)


class FilterTests(MarketplaceTestBase):
    def listing(self, **params):
        return self.client.get(reverse("marketplace:product_list"), params)

    def test_filter_by_category(self):
        response = self.listing(category="books")
        self.assertContains(response, "Story Novel")
        self.assertNotContains(response, "Blue T-Shirt")

    def test_parent_category_includes_sub_category_products(self):
        child = Category.objects.create(name="Shirts", parent=self.fashion)
        self.make_product(self.shop1, "Polo Shirt", "700.00", child)
        response = self.listing(category="fashion")
        self.assertContains(response, "Polo Shirt")
        self.assertContains(response, "Blue T-Shirt")

    def test_filter_by_shop(self):
        response = self.listing(shop=self.shop2.slug)
        self.assertContains(response, "Story Novel")
        self.assertNotContains(response, "Blue T-Shirt")

    def test_filter_by_price_range(self):
        response = self.listing(min_price="400", max_price="500")
        self.assertEqual(self.names(response), ["Blue T-Shirt"])

    def test_price_limits_include_the_exact_value(self):
        response = self.listing(min_price="450", max_price="450")
        self.assertEqual(self.names(response), ["Blue T-Shirt"])

    def test_filters_work_together(self):
        response = self.listing(category="fashion", max_price="1000")
        self.assertEqual(self.names(response), ["Blue T-Shirt"])

    def test_minimum_price_above_maximum_shows_error(self):
        response = self.listing(min_price="900", max_price="100")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Minimum price cannot be higher than maximum price.")

    def test_text_instead_of_price_shows_error(self):
        response = self.listing(min_price="abc")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a number")

    def test_negative_price_does_not_crash(self):
        self.assertEqual(self.listing(min_price="-5").status_code, 200)

    def test_unknown_shop_shows_error(self):
        response = self.listing(shop="hacker")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a valid choice")

    def test_draft_shop_is_not_offered_in_filter(self):
        response = self.listing()
        self.assertNotContains(response, "Hidden Store")

    def test_category_without_public_products_is_not_offered_in_filter(self):
        Category.objects.create(name="Empty Category")
        response = self.listing()
        self.assertNotContains(response, "Empty Category")

    def test_filters_also_apply_to_search_results(self):
        response = self.client.get(
            reverse("marketplace:search"), {"q": "shirt", "max_price": "100"}
        )
        self.assertNotContains(response, "Blue T-Shirt")


class SortTests(MarketplaceTestBase):
    def listing(self, **params):
        return self.client.get(reverse("marketplace:product_list"), params)

    def test_default_order_is_newest_first(self):
        self.assertEqual(
            self.names(self.listing()), ["Story Novel", "Denim Jacket", "Blue T-Shirt"]
        )

    def test_price_low_to_high(self):
        response = self.listing(sort="price_low")
        self.assertEqual(self.names(response), ["Story Novel", "Blue T-Shirt", "Denim Jacket"])

    def test_price_high_to_low(self):
        response = self.listing(sort="price_high")
        self.assertEqual(self.names(response), ["Denim Jacket", "Blue T-Shirt", "Story Novel"])

    def test_name_a_to_z(self):
        response = self.listing(sort="name")
        self.assertEqual(self.names(response), ["Blue T-Shirt", "Denim Jacket", "Story Novel"])

    def test_invalid_sort_shows_error(self):
        response = self.listing(sort="hacker")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a valid choice")

    def test_sorting_works_on_search_results(self):
        response = self.client.get(
            reverse("marketplace:search"), {"q": "e", "sort": "price_low"}
        )
        self.assertEqual(self.names(response), ["Story Novel", "Blue T-Shirt", "Denim Jacket"])