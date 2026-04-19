from django.contrib import admin
from django.urls import path
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),   # FIXED
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    
     # Farmer dashboard and CRUD
    path('dashboard/', views.farmer_dashboard, name='dashboard'),
    path('farmer/add/', views.add_crop, name='add_crop'),
    path('farmer/edit/<int:crop_id>/', views.edit_crop, name='edit_crop'),
    path('farmer/delete/<int:crop_id>/', views.delete_crop, name='delete_crop'),
    
    # Buyer views
     path("buyer/dashboard/", views.buyer_dashboard, name="buyer_dashboard"),
     path("buyer/crops/", views.buyer_crop_list, name="buyer_crop_list"),
     path('cart/add/<int:crop_id>/', views.add_to_cart, name='add_to_cart'),
     path('cart/', views.view_cart, name='view_cart'),
     # core/urls.py
     path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
     path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
     path('checkout/', views.checkout, name='checkout'),
     
    path("order/<int:order_id>/success/", views.order_success, name="order_success"),
    path("order/<int:order_id>/confirm/", views.confirm_payment, name="confirm_payment"),
    path("my-orders/", views.buyer_orders, name="buyer_orders"),
    path("order/confirm/<int:cart_id>/", views.confirm_order, name="confirm_order"),
    path("payment/<int:order_id>/", views.fake_payment_page, name="fake_payment"),
    path("payment/<int:order_id>/confirm/", views.fake_payment_confirm, name="fake_payment_confirm"),
    path("buyer/track/<int:order_id>/", views.track_order, name="track_order"),

    
    
    path('transporter/dashboard/', views.transporter_dashboard, name='transporter_dashboard'),
    path('transporter/claim/<int:order_id>/', views.claim_order, name='claim_order'),
    path('transporter/update/<int:transport_id>/', views.update_transport_status, name='update_transport_status'),
    path('transporter/collect/<int:transport_id>/', views.collect_cod_payment, name='collect_cod_payment'),







]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)