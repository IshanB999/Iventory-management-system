from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Products,Order
from .forms import ProductForm, OrderForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum ,Value
from django.db.models.functions import Coalesce
from django.db.models import F


# Create your views here.

@login_required
def index(request):
    orders=Order.objects.all()
    products=Products.objects.all()
    orders_count=orders.count()
    products_count=products.count()
    workers_count=User.objects.all().count()

      # Aggregated orders per product
    aggregated_orders = (
        Order.objects.values('products__name')
        .annotate(total_quantity=Sum('order_quantity'))
        .order_by('products__name')
    )

    # Products with total ordered and remaining stock
    products_with_remaining = (
        Products.objects.annotate(
            total_ordered=Coalesce(Sum('order__order_quantity'), Value(0))
        ).annotate(
            remaining=F('quantity') - F('total_ordered')
        )
    )

    if request.method=="POST":
        print(request.POST)
        form=OrderForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.staff=request.user
            
            order=form.save(commit=False)
            product=order.products
            if product.quantity >=order.order_quantity:
                product.quantity -= order.order_quantity
                product.save()
                order.save()
                instance.save()
                messages.success(request,"Order placed successfully!")
            else:
                messages.error(request,"Not enough stock available.")

            
            
        return redirect('dashboard-index')
    else:
        form=OrderForm()
    context={
        'orders':orders,
        'form':form,
        'products':products,
        'orders_count':orders_count,
        'products_count':products_count,
        'workers_count':workers_count,
        'aggregated_orders': aggregated_orders,
        'products_with_remaining': products_with_remaining,
    }
    return render(request,"dashboard/index.html",context)

@login_required
def staff(request):
    workers=User.objects.all()
    workers_count=workers.count()
    orders_count=Order.objects.all().count()
    products_count=Products.objects.all().count()
    context={
        'workers':workers,
        'workers_count':workers_count,
        'orders_count':orders_count,
        'products_count':products_count,
    }
    return render(request,"dashboard/staff.html",context)


@login_required
def staff_detail(request,pk):
    workers= User.objects.get(id=pk)
    context={
        'workers':workers,
        
    }
    return render(request,'dashboard/staff_detail.html',context)

@login_required
def product(request):
    items = Products.objects.all()
    products_count=items.count()
    # items =Products.objects.raw('SELECT * FROM dashboard_product')

    workers_count=User.objects.all().count()
    orders_count=Order.objects.all().count()
    
    if request.method =="POST":
        form=ProductForm(request.POST)
        if form.is_valid():
            form.save()
            product_name=form.cleaned_data.get('name')
            messages.success(request,f'{product_name} has been added')

            return redirect('dashboard-product')
    else:
        form=ProductForm()


    context={
        'items':items,
        'form':form,
        'workers_count':workers_count,
        'orders_count':orders_count,
        'products_count':products_count, 
              }
    return render(request,"dashboard/product.html",context)


@login_required
def product_delete(request,pk):
    item=Products.objects.get(id=pk)
    if request.method=="POST":
        item.delete()
        return redirect('dashboard-product')
    return render(request,'dashboard/product_delete.html')


@login_required
def product_update(request,pk):
    item= Products.objects.get(id=pk)
    if request.method=="POST":
     form=ProductForm(request.POST, instance=item)
     if form.is_valid():
         form.save()
         return redirect('dashboard-product')
    else:
     form=ProductForm(instance=item)

    context={
        'form':form,

    }
    return render(request,'dashboard/product_update.html',context)




@login_required
def order_list(request):
    #for detailed table of order
    orders=Order.objects.select_related('products','staff').all()

    #for aggregated table in admin page(for charts/summery)
    aggregated_orders = (
        Order.objects.values('products__name')
        .annotate(total_quantity=Sum('order_quantity'))
        .order_by('products__name')
    )

    # Products with remaining stock (subtracting orders)
    products_with_remaining = (
        Products.objects.annotate(
             total_ordered=Coalesce(Sum('order__order_quantity'), Value(0))
        ).annotate(
            remaining=F('quantity') - F('total_ordered')
        )
    )
    orders_count=Order.objects.all().count()
    products_count=Products.objects.all().count()
    workers_count=User.objects.all().count()
    

    context={
        'orders': orders,
        'aggregated_orders': aggregated_orders,
        'products_with_remaining': products_with_remaining,
        
        'workers_count':workers_count,
        'orders_count':orders_count,
        'products_count':products_count,
    }
    return render(request,"dashboard/order.html",context)