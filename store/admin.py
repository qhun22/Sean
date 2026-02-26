"""
Cấu hình Django Admin cho ứng dụng store
"""
from django.contrib import admin
from store.models import VNPayPayment

# Register your models here if you have any


@admin.register(VNPayPayment)
class VNPayPaymentAdmin(admin.ModelAdmin):
    list_display = ['order_code', 'user', 'amount', 'status', 'transaction_no', 'created_at', 'paid_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_code', 'transaction_no', 'user__email']
    readonly_fields = ['order_code', 'transaction_no', 'response_code', 'response_message', 'created_at', 'updated_at', 'paid_at']
