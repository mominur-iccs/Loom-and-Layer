from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CheckoutForm
from .models import Design, Order, OrderItem, Product, ProductColor
from .tasks import process_order

SESSION_KEY = "hoodie_selection"

def home(request):
    """Customizer + ready-made product grid, both on one page."""
    products = Product.objects.filter(is_active=True).prefetch_related("colors")
    designs = Design.objects.filter(is_active=True)

    selected_id = request.GET.get("product")
    if selected_id:
        active_product = get_object_or_404(Product, pk=selected_id, is_active=True)
    else:
        active_product = (
            products.filter(is_featured=True).first()
            or products.first()
        )

    context = {
        "products": products,
        "designs": designs,
        "active_product": active_product,
    }
    return render(request, "hoodie_app/home.html", context)


def select_options(request):
    """Customer confirmed hoodie + color + print on the home page.
    Stash the selection in the session and move to checkout."""
    if request.method != "POST":
        return redirect("hoodie_app:home")

    product = get_object_or_404(Product, pk=request.POST.get("product_id"), is_active=True)
    color = get_object_or_404(ProductColor, pk=request.POST.get("color_id"), product=product)
    design_id = request.POST.get("design_id") or None
    design = get_object_or_404(Design, pk=design_id) if design_id else None

    request.session[SESSION_KEY] = {
        "product_id": product.id,
        "color_id": color.id,
        "design_id": design.id if design else None,
    }
    return redirect("hoodie_app:checkout")


def checkout(request):
    selection = request.session.get(SESSION_KEY)
    if not selection:
        messages.info(request, "Pick a hoodie and print first.")
        return redirect("hoodie_app:home")

    product = get_object_or_404(Product, pk=selection["product_id"])
    color = get_object_or_404(ProductColor, pk=selection["color_id"])
    design = Design.objects.filter(pk=selection.get("design_id")).first()

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data["quantity"]
            unit_price = product.base_price

            with transaction.atomic():
                order = Order.objects.create(
                    customer_name=form.cleaned_data["customer_name"],
                    phone=form.cleaned_data["phone"],
                    email=form.cleaned_data.get('email'),
                    address=form.cleaned_data["address"],
                    total=unit_price * quantity,
                )
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    color=color,
                    design=design,
                    size=form.cleaned_data["size"],
                    quantity=quantity,
                    unit_price=unit_price,
                )

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
    }
    return render(request, "hoodie_app/checkout.html", context)


def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "hoodie_app/order_success.html", {"order": order})