# Wiring this into your project

1. Drop this folder in as an app named `hoodie_app` (or rename the imports throughout if you use a different name).
2. Add to `INSTALLED_APPS` and include the urls:

```python
# project/urls.py
urlpatterns = [
    ...
    path("", include("hoodie_app.urls")),
]
```

3. Settings needed:

```python
DEFAULT_FROM_EMAIL = "orders@yourdomain.com"
ORDER_NOTIFICATION_EMAIL = "you@yourdomain.com"   # where new-order alerts go
```

Plus your usual `EMAIL_BACKEND` / SMTP settings, and Celery configured as normal (broker URL, `CELERY_TASK_ALWAYS_EAGER = False` in production).

4. `python manage.py makemigrations hoodie_app && python manage.py migrate`
5. Add a `Product` (e.g. "Classic hoodie"), at least one `ProductColor`, and a few `Design` entries from the Django admin — the home page pulls directly from these, no seed data is hardcoded.
6. `print_area` on `Product` is a JSON box in percent, e.g. `{"top": 30, "left": 30, "width": 40, "height": 40}` — adjust it per product photo so the print lands on the chest, not the sleeve.

## Not included yet (flagged from the earlier design discussion)

- Phone/OTP confirmation before an order moves from `pending` to `confirmed` — worth adding given COD fraud/no-shows are common; the `Order.status` field is already there for it.
- Multiple items per order (the checkout flow is one hoodie at a time by design, for v1 simplicity). `OrderItem` already supports more if you want a real cart later.