from django.db import models
from django.contrib.auth.models import User

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

    def __str__(self):
        return f'{self.name}-{self.quantity}'
    # class Meta:
    #     verbose_name_plural="Products"




    
class Order(models.Model):
    products=models.ForeignKey(Products, on_delete=models.CASCADE,null=True)
    staff=models.ForeignKey(User,models.CASCADE,null=True)
    order_quantity=models.PositiveIntegerField(null=True)
    date=models.DateTimeField(auto_now_add=True)

    # class Meta:
    #     verbose_name_plural="order"

    def __str__(self):
        return f'{self.products} ordered by {self.staff.username}'
