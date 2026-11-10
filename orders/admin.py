from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "product_name", "unit_price", "quantity", "line_total")
    readonly_fields = ("line_total",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer", "shop", "status", "total", "created_at")
    list_filter = ("status", "shop")
    search_fields = ("order_number", "customer__username", "shipping_name")
    readonly_fields = ("order_number", "created_at", "updated_at")
    inlines = [OrderItemInline]