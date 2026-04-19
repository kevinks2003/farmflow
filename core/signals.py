from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, Transport


@receiver(post_save, sender=Order)
def notify_admin_on_new_order(sender, instance, created, **kwargs):
    """
    When a new Order is created, notify Admin by email.
    """
    if not created:
        return  # only send on new order

    subject = f"New Order #{instance.id} placed"
    message = (
        f"A new order has been placed.\n\n"
        f"Order ID: {instance.id}\n"
        f"Buyer: {instance.buyer.username}\n"
        f"Payment Method: {instance.payment_method}\n"
        f"Status: {instance.status}\n\n"
        f"Login to the Admin panel to manage this order."
    )

    # send to all ADMINS in settings.py or fallback to default email
    admin_emails = [email for _, email in getattr(settings, "ADMINS", [])]
    if not admin_emails:
        admin_emails = [settings.DEFAULT_FROM_EMAIL]

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        admin_emails,
        fail_silently=False,
    )


