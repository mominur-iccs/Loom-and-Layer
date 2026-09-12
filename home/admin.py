from django.contrib import admin

from .models import Design, Order, OrderItem, Product, ProductColor


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "base_price", "is_featured", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductColorInline]


@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "color", "design", "size", "quantity", "unit_price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "phone", "status", "total", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "created_at")
    search_fields = ("customer_name", "phone")
    inlines = [OrderItemInline]