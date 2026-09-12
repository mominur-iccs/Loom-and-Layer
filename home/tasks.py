import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Order
from .utils import build_item_preview

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_order(self, order_id):
    try:
        order = Order.objects.prefetch_related(
            "items__product", "items__color", "items__design"
        ).get(pk=order_id)
    except Order.DoesNotExist:
        return

    if order.notified_at:
        return

    try:
        item_lines = []
        attachments = []

        for item in order.items.all():
            item_lines.append(
                f"- {item.product.name} ({item.color.name}, size {item.size}) x{item.quantity}"
                + (f", print: {item.design.name}" if item.design else "")
            )

            if not item.preview_image:
                preview = build_item_preview(item)
                if preview:
                    suffix = item.design.slug if item.design and hasattr(item.design, "slug") else "plain"
                    filename = f"order_{order.id}_item_{item.id}_{item.product.slug}_{suffix}.jpg"
                    item.preview_image.save(filename, preview, save=True)

            if item.preview_image:
                try:
                    with item.preview_image.open("rb") as f:
                        attachments.append(
                            (f"order_{order.id}_item_{item.id}.jpg",
                            f.read(), "image/jpeg")
                        )
                except FileNotFoundError:
                    pass

        has_previews = bool(attachments)
        total_kb = sum(len(c) for _, c, _ in attachments) / 1024
        logger.info("Order %s: %d attachment(s), %.1f KB",
                    order.id, len(attachments), total_kb)

        # --- Team email ---
        team_context = {"order": order, "has_previews": has_previews}
        team_subject = f"New hoodie order #{order.id}"
        team_text = "\n".join(
            [f"New order #{order.id} from {order.customer_name}", ""]
            + item_lines
            + [
                "",
                f"Total: {order.total}",
                f"Phone: {order.phone}",
                f"Email: {order.email or '—'}",
                f"Address: {order.address}",
            ]
        )
        team_html = render_to_string("emails/order_team.html", team_context)

        team_email = EmailMultiAlternatives(
            subject=team_subject,
            body=team_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ORDER_NOTIFICATION_EMAIL],
        )
        team_email.attach_alternative(team_html, "text/html")
        for filename, content, mimetype in attachments:
            team_email.attach(filename, content, mimetype)
        team_email.send()

        # --- Customer email ---
        if order.email:
            customer_context = {"order": order, "has_previews": has_previews}
            customer_subject = f"Your Hoodie Co. order #{order.id} is confirmed"
            customer_text = "\n".join(
                [
                    f"Hi {order.customer_name},",
                    "",
                    f"Thanks for order #{order.id}! Here's what we've got for you:",
                    "",
                ]
                + item_lines
                + [
                    "",
                    f"Total: Tk {order.total} (cash on delivery)",
                    "",
                    f"We'll call you at {order.phone} shortly to confirm, then pack and ship.",
                    "The attached image shows exactly how your design will look.",
                    "",
                    "— Hoodie Co.",
                ]
            )
            customer_html = render_to_string("emails/order_customer.html", customer_context)

            customer_email = EmailMultiAlternatives(
                subject=customer_subject,
                body=customer_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.email],
                reply_to=[settings.ORDER_NOTIFICATION_EMAIL],
            )
            customer_email.attach_alternative(customer_html, "text/html")
            for filename, content, mimetype in attachments:
                customer_email.attach(filename, content, mimetype)
            customer_email.send()

        order.notified_at = timezone.now()
        order.save(update_fields=["notified_at"])

    except Exception as exc:
        raise self.retry(exc=exc)