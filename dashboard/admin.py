from django.contrib import admin
from .models import Products,Order
from django.contrib.auth.models import Group


admin.site.site_header="KenInventory Dashboard"

class ProductsAdmin(admin.ModelAdmin):
    list_display=('name','category','quantity',)
    list_filter=("category",)


# class orderAdmin(admin.ModelAdmin):
#     list_display=('Products','staff','order_quantity','date')
    

# Register your models here.
admin.site.register(Products,ProductsAdmin)

admin.site.register(Order)
