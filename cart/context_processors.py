from .cart import CART_SESSION_KEY


def cart_summary(request):
    items = request.session.get(CART_SESSION_KEY, {})
    return {"cart_count": sum(items.values())}