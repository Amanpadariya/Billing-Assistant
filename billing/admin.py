from django.contrib import admin
from .models import Bill, BillItem


class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 1


class BillAdmin(admin.ModelAdmin):
    inlines = [BillItemInline]
    list_display = ("invoice_number", "customer", "created_at", "payment_status")


admin.site.register(Bill, BillAdmin)
admin.site.register(BillItem)
