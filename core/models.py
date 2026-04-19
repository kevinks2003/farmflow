from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, role="farmer", **extra_fields):
        if not username:
            raise ValueError("The Username is required")
        if not email:
            raise ValueError("The Email is required")

        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            role=role,
            **extra_fields
        )
        user.set_password(password)  # ✅ properly hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        if not password:
            raise ValueError("Superuser must have a password")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, role="admin", **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = (
        ("farmer", "Farmer"),
        ("buyer", "Buyer"),
        ("transporter", "Transporter"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="farmer")
    place = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=10, blank=True, null=True)  # ✅ new field


    objects = UserManager()  # ✅ attach custom manager

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    # ======================== FARMER CROP MODEL ========================



class Crop(models.Model):
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="crops"
    )
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="crops/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.farmer.username})"
    
    # ======================== buyer MODEL ========================

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        null=True, blank=True  # ✅ allow existing rows without user
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def total_price(self):
        # Sum the total_price of all items in the cart
        return sum(item.total_price() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.crop.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.crop.name}"
    
    # core/models.py
class Order(models.Model):
    PAYMENT_CHOICES = [
        ("COD", "Cash on Delivery"),
        ("ONLINE", "Online Payment"),
    ]

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default="COD")
    is_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    
    
     # ✅ NEW FIELD
    is_approved = models.BooleanField(default=False)

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    def __str__(self):
        return f"Order {self.id} by {self.buyer.username} ({self.payment_method})"

class OrderItem(models.Model):
    order = models.ForeignKey("Order", related_name="items", on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot price

    def total_price(self):
        return self.price * self.quantity
    

class Transport(models.Model):
    STATUS_CHOICES = (
        ("assigned", "Assigned"),       # order given to transporter
        ("picked_up", "Picked Up"),     # transporter picked up from farmer
        ("in_transit", "In Transit"),   # on the way
        ("delivered", "Delivered"),
    )

    order = models.OneToOneField(
        "Order", on_delete=models.CASCADE, related_name="transport"
    )
    transporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"role": "transporter"},
    )
    vehicle_details = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default="assigned"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transport for Order #{self.order.id} ({self.status})"


# core/models.py (add near other models)

class TransporterProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transporterprofile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    place = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    vehicle_number = models.CharField(max_length=30, blank=True, null=True)
    is_available = models.BooleanField(default=True)  # set false if transporter is unavailable

    def __str__(self):
        return f"Transporter: {self.user.username} ({self.district})"



    
  