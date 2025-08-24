from django import forms
from .models import Products, Order


class ProductForm(forms.ModelForm):
    class Meta:
        model=Products
        fields=['name','category','quantity']

class OrderForm(forms.ModelForm):
    class Meta:
        model=Order
        fields=['products','order_quantity']
