from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', views.home, name="home"),
    # path('fetch_item/<str:item_id>', views.fetch_item, name="fetch"),
    # path('add_item', views.add_item, name="add_item"),
    path('payment/create/', views.create_payment, name='create_payment'),
    path('payment/success/', views.execute_payment, name='execute_payment'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    
]