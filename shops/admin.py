from django.contrib import admin

from .models import Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "category", "is_published", "created_at")
    list_filter = ("is_published", "category")
    search_fields = ("name", "owner__username")