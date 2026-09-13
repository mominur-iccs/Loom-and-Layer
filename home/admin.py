from django.contrib import admin

from .models import Design, Order, OrderItem, Product, ProductColor, ProductVariant


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 0


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    autocomplete_fields = ["color"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "base_price", "is_active", "is_featured"]
    list_filter = ["category", "is_active", "is_featured"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductColorInline, ProductVariantInline]


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ["name", "product", "hex_code", "is_default"]
    list_filter = ["product", "is_default"]
    search_fields = ["name", "product__name"]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["product", "color", "size", "stock", "is_active"]
    list_filter = ["product", "color", "size", "is_active"]
    list_editable = ["stock", "is_active"]
    search_fields = ["product__name", "color__name"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "color", "variant", "design", "size", "quantity", "unit_price", "preview_image"]
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "customer_name", "phone", "status", "total", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["customer_name", "phone", "email"]
    readonly_fields = ["total", "created_at", "notified_at", "inventory_released_at"]
    inlines = [OrderItemInline]


@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name"]
