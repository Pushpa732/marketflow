from django.urls import path

from . import views, views_import

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("add/", views.product_create, name="product_create"),
    path("import/", views_import.product_import, name="product_import"),
    path("import/template/", views_import.product_import_template, name="product_import_template"),
    path("<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("<int:pk>/images/", views.product_images, name="product_images"),
    path(
        "<int:pk>/images/<int:image_pk>/delete/",
        views.product_image_delete,
        name="product_image_delete",
    ),
]