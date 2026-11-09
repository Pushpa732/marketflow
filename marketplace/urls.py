from django.urls import path

from . import views

app_name = "marketplace"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("products/", views.product_list, name="product_list"),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
    path("shops/", views.shop_list, name="shop_list"),
    path("shops/<slug:slug>/", views.shop_detail, name="shop_detail"),
]