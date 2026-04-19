from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Crop, Order, OrderItem
from django.contrib.auth.decorators import login_required
from .forms import CropForm
from django.db.models import Q
from .models import Crop, Cart, CartItem
from decimal import Decimal
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .forms import CustomUserCreationForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import random
from .models import Transport, TransporterProfile
from .utils import notify_buyer_transport_update, notify_buyer_payment_collected
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt







User = get_user_model()

def home(request):
    return render(request, "home.html")

def dashboard(request):
    return render(request, "dashboard.html")


def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Account created successfully! Please login.")
            return redirect("login")
        else:
            messages.error(request, "⚠️ Please fix the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back {username} 👋")
           
            # Redirect based on role
            if user.role == "farmer":
                return redirect("dashboard")
            elif user.role == "buyer":
                return redirect("buyer_crop_list")  # you'll create this later
            elif user.role == "transporter":
                return redirect("transporter_dashboard")
        else:
            messages.error(request, "Invalid username or password")
            return redirect("login")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")

# List all crops for the logged-in farmer
@login_required
def farmer_dashboard(request):
    crops = Crop.objects.filter(farmer=request.user)
    return render(request, "dashboard.html", {"crops": crops})

@login_required
def add_crop(request):
    if request.method == "POST":
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.farmer = request.user  # link crop to logged-in farmer
            crop.save()
            return redirect("dashboard")
    else:
        form = CropForm()
    return render(request, "add_crop.html", {"form": form})


@login_required
def edit_crop(request, crop_id):
    crop = get_object_or_404(Crop, id=crop_id, farmer=request.user)  # make sure only farmer can edit

    if request.method == "POST":
        form = CropForm(request.POST, request.FILES, instance=crop)
        if form.is_valid():
            form.save()
            return redirect("dashboard")  # after saving go back to farmer dashboard
    else:
        form = CropForm(instance=crop)

    return render(request, "edit_crop.html", {"form": form})

@login_required
def delete_crop(request, crop_id):
    crop = get_object_or_404(Crop, id=crop_id, farmer=request.user)

    if request.method == "POST":
        crop.delete()
        messages.success(request, "Crop deleted successfully!")
        return redirect("dashboard")

    return render(request, "confirm_delete.html", {"crop": crop})

# Buyer Crop List + Search
def buyer_crop_list(request):
    query = request.GET.get("q")
    crops = Crop.objects.all()

    if query:
        crops = crops.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(price__icontains=query)
        )

    return render(request, "buyer_crop_list.html", {"crops": crops, "query": query})
@login_required
def buyer_dashboard(request):
    return render(request, "buyer_dashboard.html")

@login_required
def add_to_cart(request, crop_id):
    crop = get_object_or_404(Crop, id=crop_id)

    # get or create a cart for the logged-in buyer
    cart, created = Cart.objects.get_or_create(user=request.user)

    # check if crop already in cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, crop=crop)

    if not created:
        # already in cart → increase quantity
        cart_item.quantity += 1
        cart_item.save()

    return redirect('view_cart') 

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()

    total_price = sum(item.crop.price * item.quantity for item in cart_items)

    return render(request, 'view_cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
    })
    
    # core/views.py
@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    return redirect('view_cart')

@login_required
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == "POST":
        new_quantity = int(request.POST.get("quantity", 1))

        # Check stock
        if new_quantity > item.crop.quantity:
            messages.error(request, f"Only {item.crop.quantity} available in stock.")
            new_quantity = item.crop.quantity

        if new_quantity <= 0:
            item.delete()
            messages.success(request, "Item removed from cart.")
        else:
            item.quantity = new_quantity
            item.save()
            messages.success(request, "Cart updated successfully!")

    return redirect("view_cart")


@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    total_price = sum(item.total_price() for item in cart_items)

    return render(request, "checkout.html", {
        "cart": cart,
        "cart_items": cart_items,
        "total_price": total_price,
    })



@login_required
def confirm_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)

    if request.method == "POST":
        order.is_paid = True
        order.status = "Processing"   # Or "Paid"
        order.save()

        # ✅ clear cart items after successful payment
        order.cart.items.all().delete()

        messages.success(request, f"🎉 Payment successful! Your Order #{order.id} has been placed.")
        return redirect("order_success", order_id=order.id)

    return redirect("checkout")

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    return render(request, "order_success.html", {"order": order})

@login_required
def buyer_orders(request):
    orders = Order.objects.filter(buyer=request.user).prefetch_related('transport').order_by("-created_at")
    return render(request, "buyer_orders.html", {"orders": orders})


@login_required
def confirm_order(request, cart_id):
    cart = get_object_or_404(Cart, id=cart_id, user=request.user)

    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "COD")

        # Create order with default status ("Pending")
        order = Order.objects.create(
            buyer=request.user,
            payment_method=payment_method,
            status="Pending"  # will be approved by admin later
        )

        # Copy cart items into order items
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                crop=item.crop,
                quantity=item.quantity,
                price=item.crop.price,  # snapshot of current price
            )

            # Reduce crop stock
            item.crop.quantity -= item.quantity
            item.crop.save()

        # Clear the cart
        cart.items.all().delete()

        # Email notification to admin (optional)
        subject = f"📦 New Order #{order.id} - FarmFlow"
        html_message = render_to_string("order_notification.html", {
            "order": order,
            "buyer": order.buyer,
        })
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = ["kevinshaju577@gmail.com"]  # admin email

        send_mail(
            subject,
            plain_message,
            from_email,
            to_email,
            html_message=html_message,
        )

        # ✅ Redirect based on payment method
        messages.success(request, f"Order #{order.id} confirmed! Waiting for admin approval.")

        if payment_method == "ONLINE":
            return redirect("fake_payment", order_id=order.id)
        else:
            return redirect("order_success", order_id=order.id)

@login_required
def fake_payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)

    if order.payment_method != "ONLINE":
        return redirect("order_success", order_id=order.id)

    return render(request, "payment.html", {
        "order": order,
        "amount": order.total_price(),
    })


@login_required
@csrf_exempt
def fake_payment_confirm(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)

    if request.method == "POST":
        # Simulate processing
        order.is_paid = True
        order.status = "Processing"
        order.save()

        messages.success(request, f"✅ Payment successful for Order #{order.id}")
        return redirect("order_success", order_id=order.id)

    return redirect("fake_payment", order_id=order.id)



    # Handle GET request if needed

def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    return render(request, "order_success.html", {"order": order})

def is_transporter(user):
    return user.is_authenticated and user.role == 'transporter'

@login_required
@user_passes_test(is_transporter)
def transporter_dashboard(request):
    user = request.user
    try:
        profile = user.transporterprofile
        my_district = profile.district
    except TransporterProfile.DoesNotExist:
        my_district = user.district

    # Orders in the transporter's district that are accepted and unassigned
    available_orders = Order.objects.filter(
        status="Accepted",
        transport__isnull=True,
        buyer__district__iexact=my_district
    ).select_related('buyer').prefetch_related('items__crop')

    # Orders from other districts where there are no active transporters
    extra_orders = []
    for order in Order.objects.filter(status="Accepted", transport__isnull=True).select_related('buyer').prefetch_related('items__crop'):
        if not User.objects.filter(role="transporter", district=order.buyer.district, is_active=True).exists():
            if order not in available_orders:
                extra_orders.append(order)

    available_orders = list(available_orders) + extra_orders
    available_orders.sort(key=lambda x: x.created_at, reverse=True)

    # Orders already claimed by this transporter
    my_transports = Transport.objects.filter(
        transporter=user
    ).select_related('order__buyer').prefetch_related('order__items__crop').order_by('-assigned_at')

    return render(request, 'transporter_dashboard.html', {
        'available_orders': available_orders,
        'my_transports': my_transports,
        'my_district': my_district,
    })




@login_required
@user_passes_test(is_transporter)
def claim_order(request, order_id):
    user = request.user

    if request.method == "POST":
        try:
            with transaction.atomic():  # start a transaction
                # Lock the order for this transaction
                order = Order.objects.select_for_update().get(id=order_id, status="Accepted")

                # Check if already claimed
                if hasattr(order, 'transport'):
                    messages.error(request, "Order already claimed.")
                    return redirect('transporter_dashboard')

                # Create Transport
                Transport.objects.create(order=order, transporter=user, status='assigned')

                messages.success(request, f"You claimed Order #{order.id}.")
                notify_buyer_transport_update(order, 'assigned', user)

        except Order.DoesNotExist:
            messages.error(request, "Order not available.")
    
    return redirect('transporter_dashboard')




@login_required
@user_passes_test(is_transporter)
def update_transport_status(request, transport_id):
    transport = get_object_or_404(Transport, id=transport_id, transporter=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        # allowed statuses from model: 'assigned', 'in_progress', 'delivered'
        if new_status in dict(Transport.STATUS_CHOICES).keys():
            transport.status = new_status
            transport.save()

            # If delivered and payment method is COD, we may mark order as paid later via a 'collect_payment' action
            # notify buyer
            notify_buyer_transport_update(transport.order, transport.status, request.user)
            messages.success(request, f'Order #{transport.order.id} status updated to {transport.status}.')
        else:
            messages.error(request, 'Invalid status.')
    return redirect('transporter_dashboard')

@login_required
@user_passes_test(is_transporter)
def collect_cod_payment(request, transport_id):
    transport = get_object_or_404(Transport, id=transport_id, transporter=request.user)
    order = transport.order
    if order.payment_method == "COD" and not order.is_paid:
        order.is_paid = True
        order.save()
        messages.success(request, f'COD payment recorded for Order #{order.id}.')
        # notify buyer about payment collected
        notify_buyer_payment_collected(order, request.user)
    else:
        messages.info(request, 'Order is already paid or not COD.')
    return redirect('transporter_dashboard')

@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    transport = getattr(order, "transport", None)
    return render(request, "buyer/track_order.html", {"order": order, "transport": transport})



