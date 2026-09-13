from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CheckoutForm
from .models import Design, Order, OrderItem, Product, ProductColor, ProductVariant
from .tasks import process_order

SESSION_KEY = "hoodie_selection"


def home(request):
    products = Product.objects.filter(is_active=True).prefetch_related("colors", "variants")
    product_cards = ProductColor.objects.filter(
        product__is_active=True,
        variants__is_active=True,
        variants__stock__gt=0,
    ).select_related("product").distinct()
    designs = Design.objects.filter(is_active=True)

    selected_id = request.GET.get("product")
    selected_color_id = request.GET.get("color")

    if selected_id:
        active_product = get_object_or_404(Product, pk=selected_id, is_active=True)
    else:
        active_product = products.filter(is_featured=True).first() or products.first()

    selected_color = None
    if active_product and selected_color_id:
        selected_color = active_product.colors.filter(pk=selected_color_id).first()

    context = {
        "products": products,
        "product_cards": product_cards,
        "designs": designs,
        "active_product": active_product,
        "selected_color_id": selected_color.id if selected_color else None,
        "size_guide": getattr(settings, "HOODIE_SIZE_GUIDE", []),
        "variant_data": [
            {
                "id": variant.id,
                "color_id": variant.color_id,
                "size": variant.size,
                "stock": variant.stock,
            }
            for variant in active_product.variants.filter(is_active=True, stock__gt=0)
        ] if active_product else [],
    }
    return render(request, "hoodie_app/home.html", context)


def select_options(request):
    if request.method != "POST":
        return redirect("hoodie_app:home")

    product = get_object_or_404(Product, pk=request.POST.get("product_id"), is_active=True)
    color = get_object_or_404(ProductColor, pk=request.POST.get("color_id"), product=product)
    design_id = request.POST.get("design_id") or None
    design = get_object_or_404(Design, pk=design_id, is_active=True) if design_id else None
    variant = get_object_or_404(
        ProductVariant,
        pk=request.POST.get("variant_id"),
        product=product,
        color=color,
        is_active=True,
        stock__gt=0,
    )

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1 or quantity > min(10, variant.stock):
        messages.error(request, "Quantity must be between 1 and 10.")
        return redirect("hoodie_app:home")

    request.session[SESSION_KEY] = {
        "product_id": product.id,
        "color_id": color.id,
        "design_id": design.id if design else None,
        "variant_id": variant.id,
        "size": variant.size,
        "quantity": quantity,
    }
    return redirect("hoodie_app:checkout")


def checkout(request):
    selection = request.session.get(SESSION_KEY)
    if not selection:
        messages.info(request, "Choose your hoodie options first.")
        return redirect("hoodie_app:home")

    product = get_object_or_404(Product, pk=selection["product_id"], is_active=True)
    color = get_object_or_404(ProductColor, pk=selection["color_id"], product=product)
    variant = get_object_or_404(ProductVariant, pk=selection["variant_id"], product=product, color=color, is_active=True)
    design = Design.objects.filter(pk=selection.get("design_id"), is_active=True).first()
    size = selection["size"]
    quantity = selection["quantity"]
    order_total = product.base_price * quantity

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                variant = ProductVariant.objects.select_for_update().get(pk=variant.pk)
                if variant.stock < quantity:
                    messages.error(request, f"Only {variant.stock} item(s) remain in this size.")
                    return redirect("hoodie_app:home")

                order = Order.objects.create(
                    customer_name=form.cleaned_data["customer_name"],
                    phone=form.cleaned_data["phone"],
                    email=form.cleaned_data.get("email"),
                    address=form.cleaned_data["address"],
                    total=order_total,
                )
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    color=color,
                    variant=variant,
                    design=design,
                    size=variant.size,
                    quantity=quantity,
                    unit_price=product.base_price,
                )
                ProductVariant.objects.filter(pk=variant.pk).update(stock=F("stock") - quantity)

            del request.session[SESSION_KEY]
            process_order.delay(order.id)
            return redirect("hoodie_app:order_success", order_id=order.id)
    else:
        form = CheckoutForm()

    context = {
        "form": form,
        "product": product,
        "color": color,
        "design": design,
        "size": size,
        "quantity": quantity,
        "order_total": order_total,
        "print_area": product.print_area,
        "delivery_note": getattr(settings, "ORDER_DELIVERY_NOTE", "Delivery charge and estimated time will be confirmed by phone."),
        "exchange_note": getattr(settings, "ORDER_EXCHANGE_NOTE", "Size exchange availability will be confirmed before shipping."),
    }
    return render(request, "hoodie_app/checkout.html", context)


def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "hoodie_app/order_success.html", {"order": order})
