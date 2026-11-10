from decimal import Decimal

from catalog.models import Product

CART_SESSION_KEY = "cart"
MAX_QUANTITY_PER_ITEM = 99


class Cart:
    """A shopping cart stored in the visitor's session as {product_id: quantity}."""

    def __init__(self, request):
        self.session = request.session
        self._items = dict(self.session.get(CART_SESSION_KEY, {}))
        self.notices = []

    def _save(self):
        self.session[CART_SESSION_KEY] = self._items
        self.session.modified = True

    def quantity_of(self, product):
        return self._items.get(str(product.pk), 0)

    def set_quantity(self, product, quantity):
        """Set the quantity (never above the stock). Returns the quantity really saved."""
        key = str(product.pk)
        allowed = min(quantity, product.stock, MAX_QUANTITY_PER_ITEM)
        if allowed > 0:
            self._items[key] = allowed
        else:
            allowed = 0
            self._items.pop(key, None)
        self._save()
        return allowed

    def add(self, product, quantity=1):
        return self.set_quantity(product, self.quantity_of(product) + quantity)

    def remove(self, product_id):
        self._items.pop(str(product_id), None)
        self._save()

    def clear(self):
        self._items = {}
        self._save()

    @property
    def count(self):
        return sum(self._items.values())

    def lines(self):
        """Return the cart lines with fresh prices from the database.

        Items that are no longer for sale are removed, and quantities above the
        current stock are reduced. Explanations are added to self.notices.
        """
        ids = [int(key) for key in self._items]
        products = (
            Product.objects.filter(pk__in=ids, is_published=True, shop__is_published=True)
            .select_related("shop")
            .prefetch_related("images")
        )
        by_id = {product.pk: product for product in products}

        lines = []
        changed = False
        for key, quantity in list(self._items.items()):
            product = by_id.get(int(key))

            if product is None:
                del self._items[key]
                changed = True
                self.notices.append("An item in your cart is no longer available and was removed.")
                continue

            if product.stock <= 0:
                del self._items[key]
                changed = True
                self.notices.append(f"'{product.name}' is out of stock and was removed from your cart.")
                continue

            if quantity > product.stock:
                quantity = product.stock
                self._items[key] = quantity
                changed = True
                self.notices.append(
                    f"Only {product.stock} of '{product.name}' are in stock, so the quantity was reduced."
                )

            lines.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "unit_price": product.price,
                    "line_total": product.price * quantity,
                }
            )

        if changed:
            self._save()
        return lines

    def groups(self):
        """Group the lines by shop, with a subtotal for each shop."""
        grouped = {}
        for line in self.lines():
            shop = line["product"].shop
            group = grouped.setdefault(
                shop.pk, {"shop": shop, "lines": [], "subtotal": Decimal("0")}
            )
            group["lines"].append(line)
            group["subtotal"] += line["line_total"]
        return list(grouped.values())