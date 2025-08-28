from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
timezone.now


# Create your models here.

CATEGORY=(
    ("Stationary","Stationary"),
    ("Electronics","Electronics"),
    ("Groceries","Groceries"),
)


class Products(models.Model):
    name=models.CharField(max_length=100,null=True)
    category=models.CharField(max_length=200,choices=CATEGORY,null=True)
    quantity=models.PositiveIntegerField(null=True)
    created_by = models.ForeignKey(User, related_name='created_products', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, related_name='updated_products', on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f'{self.name}-{self.quantity}'
    # class Meta:
    #     verbose_name_plural="Products"




    
class Order(models.Model):
    products=models.ForeignKey(Products, on_delete=models.CASCADE,null=True)
    staff=models.ForeignKey(User,models.CASCADE,null=True)
    order_quantity=models.PositiveIntegerField(null=True)
    date=models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # optional if you want order price
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # <- total payment
    payment_date = models.DateField(auto_now_add=True)

    # class Meta:
    #     verbose_name_plural="order"

    def __str__(self):
        return f'{self.products} ordered by {self.staff.username}'
