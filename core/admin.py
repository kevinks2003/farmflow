
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Crop, Cart, CartItem, Order, OrderItem, Transport
from .models import TransporterProfile
from django.core.mail import send_mail
from django.conf import settings
        

# ---------- User Admin ----------
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("FarmFlow Info", {"fields": ("role", "place", "district")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("FarmFlow Info", {"fields": ("role", "place", "district")}),
    )
    list_display = ("username", "email", "role", "place", "district", "is_staff", "date_joined")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "place", "district")
    ordering = ("username",)


# ---------- Crop Admin ----------
@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "farmer", "quantity", "price", "created_at")
    list_filter = ("farmer", "created_at")
    search_fields = ("name", "farmer__username")
    ordering = ("-created_at",)


# ---------- Cart Item Inline ----------
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "total_price")
    inlines = [CartItemInline]


# ---------- Order Item Inline ----------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


# ---------- Transport Inline ----------
class TransportInline(admin.TabularInline):
    model = Transport
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "transporter":
            kwargs["queryset"] = User.objects.filter(role="transporter")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ---------- Order Admin ----------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "payment_method", "is_paid", "status", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("buyer__username", "id")
    ordering = ("-created_at",)
    inlines = [OrderItemInline, TransportInline]

    actions = ["mark_accepted", "mark_rejected"]

    # ---- Accept Orders ----
    def mark_accepted(self, request, queryset):
        for order in queryset:
            if order.status != "Accepted":
                order.status = "Accepted"
                order.save()

                # Notify transporters in buyer's district
                district_transporters = User.objects.filter(
                    role="transporter",
                    district=order.buyer.district,
                    is_active=True
                )

                # If no transporters in district, notify all active transporters
                if district_transporters.exists():
                    recipients = district_transporters
                else:
                    recipients = User.objects.filter(role="transporter", is_active=True)

                for t in recipients:
                    send_mail(
                        subject=f"Order #{order.id} Available for Assignment",
                        message=f"Hello {t.username},\n\n"
                                f"Order #{order.id} has been approved by the admin.\n"
                                f"Buyer: {order.buyer.username}\n"
                                f"District: {order.buyer.district}\n"
                                f"Payment: {order.payment_method}\n\n"
                                f"Please claim this order if you want to deliver it.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[t.email],
                        fail_silently=False,
                    )

        self.message_user(request, "Selected orders have been approved and transporters notified.")
    mark_accepted.short_description = "✅ Approve selected orders and notify transporters"

    # ---- Reject Orders ----
    def mark_rejected(self, request, queryset):
        updated = queryset.update(status="Rejected")
        self.message_user(request, f"{updated} order(s) marked as Rejected.")
    mark_rejected.short_description = "❌ Reject selected orders"


# ---------- Transport Admin ----------
@admin.register(Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "transporter", "status", "assigned_at", "updated_at")
    list_filter = ("status", "transporter")
    search_fields = ("order__id", "transporter__username")
    ordering = ("-assigned_at",)

@admin.register(TransporterProfile)
class TransporterProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'district', 'is_available', 'vehicle_number')
    search_fields = ('user__username', 'district')