from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "method", "status", "amount", "transaction_id", "paid_at")
    list_filter = ("method", "status")
    search_fields = ("order__order_number", "transaction_id")
    readonly_fields = ("paid_at", "created_at", "updated_at")