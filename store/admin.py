from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *  # Import your Customer model


    
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ShippingAddress)
admin.site.register(Coupon)
admin.site.register(Category)
admin.site.register(SubCategory)


# Unregister the Customer model if it's already registered
admin.site.unregister(Customer)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'email']

@receiver(post_save, sender=User)
def create_or_update_customer_for_user(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance, name=instance.username, email=instance.email)
    else:
        # If the User instance is updated, update the corresponding Customer instance
        customer, created = Customer.objects.get_or_create(user=instance)
        if not created:
            customer.name = instance.username
            customer.email = instance.email
            customer.save()

