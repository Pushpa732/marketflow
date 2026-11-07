from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("add/", views.product_create, name="product_create"),
    path("<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("<int:pk>/images/", views.product_images, name="product_images"),
    path(
        "<int:pk>/images/<int:image_pk>/delete/",
        views.product_image_delete,
        name="product_image_delete",
    ),
]