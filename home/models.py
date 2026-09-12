from django.db import models, transaction

SIZE_CHOICES = [
    ("S", "Small"),
    ("M", "Medium"),
    ("L", "Large"),
    ("XL", "X-Large"),
]

ORDER_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("confirmed", "Confirmed"),
    ("packed", "Packed"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
]


class Product(models.Model):
    """A base garment type. Only 'hoodie' for now, but this stays generic
    on purpose so adding a t-shirt or mug later is just a new row."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=50, default="hoodie")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    is_featured = models.BooleanField(
        default=False,
        help_text="Show this product in the customizer by default. Only one product can be featured.",
    )

    # % box describing where a print renders on this product's color images,
    # e.g. {"top": 30, "left": 30, "width": 40, "height": 40}
    print_area = models.JSONField(
        default=dict,
        help_text="Percent-based box {top, left, width, height} for print placement",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_featured:
                Product.objects.filter(is_featured=True).exclude(pk=self.pk).update(is_featured=False)
            super().save(*args, **kwargs)


class ProductColor(models.Model):
    product = models.ForeignKey(Product, related_name="colors", on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    hex_code = models.CharField(max_length=7, help_text="e.g. #2C2C2A")
    image = models.ImageField(upload_to="products/colors/")
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "name"]

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class Design(models.Model):
    """The print catalog users can choose from."""

    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="designs/")
    thumbnail = models.ImageField(upload_to="designs/thumbs/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Order(models.Model):
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(max_length=100, blank=True)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default="pending")
    total = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    color = models.ForeignKey(ProductColor, on_delete=models.PROTECT)
    design = models.ForeignKey(Design, blank=True, null=True, on_delete=models.SET_NULL)
    size = models.CharField(max_length=5, choices=SIZE_CHOICES, default="M")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    preview_image = models.ImageField(
        upload_to="orders/previews/",
        blank=True,
        null=True,
        help_text="Auto-generated composite of the color image + design, for the packing team.",
    )

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product.name} x{self.quantity} ({self.size})"