from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def notify_buyer_transport_update(order, status, transporter_user):
    subject = f"Order #{order.id} update: {status}"
    html_message = render_to_string('transport_update.html', {
        'order': order,
        'status': status,
        'transporter': transporter_user,
        'buyer': order.buyer,
    })
    plain = strip_tags(html_message)
    to = [order.buyer.email] if order.buyer.email else []
    if to:
        send_mail(subject, plain, settings.DEFAULT_FROM_EMAIL, to, html_message=html_message)

def notify_buyer_payment_collected(order, transporter_user):
    subject = f"Order #{order.id}: Payment Collected"
    html_message = render_to_string('payment_collected.html', {
        'order': order,
        'transporter': transporter_user,
        'buyer': order.buyer,
    })
    send_mail(subject, strip_tags(html_message), settings.DEFAULT_FROM_EMAIL, [order.buyer.email], html_message=html_message)
