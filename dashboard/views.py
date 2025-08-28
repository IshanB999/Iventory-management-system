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
from django.db.models import Q
import stripe
from django.conf import settings
from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models.functions import TruncDay
from datetime import date
from django.db.models.functions import ExtractMonth
import datetime
import openpyxl
from .forms import UploadExcelForm

# Create your views here.


@login_required
def index(request):
    orders = Order.objects.all()
    products = Products.objects.all()
    orders_count = orders.count()
    products_count = products.count()
    workers_count = User.objects.all().count()

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

    today=datetime.date.today()
    payments_by_day = (
        Order.objects.filter(payment_date__year=today.year, payment_date__month=today.month)
        .annotate(day=TruncDay('payment_date'))
        .values('day')
        .annotate(total_payment=Sum('payment_amount'))
        .order_by('day')
    )

    payment_labels = [p['day'].strftime('%d %b') for p in payments_by_day]
    payment_data = [float(p['total_payment']) for p in payments_by_day]

    # Always initialize the form
    form = OrderForm()

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.staff = request.user
            product = order.products

            # Stock check
            if product.quantity >= order.order_quantity:
                # --- Stripe Integration ---
                import stripe
                stripe.api_key = settings.STRIPE_SECRET_KEY
                YOUR_DOMAIN = "http://127.0.0.1:8000"

                line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {'name': product.name},
                            'unit_amount': int(product.price * 100) * order.order_quantity,
                        },
                        'quantity': 1,
                    }],
                print(line_items)
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {'name': product.name},
                            'unit_amount': int(product.price * 100) * order.order_quantity,
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=YOUR_DOMAIN + f'/dashboard/order-success/{product.id}/{order.order_quantity}/',
                    cancel_url=YOUR_DOMAIN + '/dashboard/',
                )
                return redirect(checkout_session.url)
            else:
                messages.error(request, "Not enough stock available.")
                return redirect('dashboard-index')

    # Render page for GET requests or if form is invalid POST
    context = {
        'orders': orders,
        'form': form,
        'products': products,
        'orders_count': orders_count,
        'products_count': products_count,
        'workers_count': workers_count,
        'aggregated_orders': aggregated_orders,
        'products_with_remaining': products_with_remaining,
        'payment_labels': payment_labels,  # <-- for chart
        'payment_data': payment_data, 
    }
    return render(request, "dashboard/index.html", context)


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
    query=request.GET.get('query')
    if query:
        items = Products.objects.filter(
            Q(name__icontains=query) | Q(category__icontains=query)
        )
    else:
        items=Products.objects.all()

    all_products=Products.objects.values_list('name',flat=True).distinct()
    # items = Products.objects.all()
    products_count=items.count()
    # items =Products.objects.raw('SELECT * FROM dashboard_product')

    workers_count=User.objects.all().count()
    orders_count=Order.objects.all().count()
    
    if request.method == "POST":
        form = ProductForm(request.POST,request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.updated_by = request.user
        if not product.pk:
            product.created_by = request.user
        product.save()
        messages.success(request, f'{product.name} has been saved')
        return redirect('dashboard-product')
    else:
        form = ProductForm()



    context={
        'items':items,
        'form':form,
        'workers_count':workers_count,
        'orders_count':orders_count,
        'products_count':products_count, 
        'query':query,
        'all_products':all_products,
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


def product_orders(request,pk):
    product=Products.objects.get(id=pk)
    orders=Order.objects.filter(products=product).select_related('staff')
    total_ordered=orders.aggregate(total=Coalesce(Sum('order_quantity'),Value(0)))['total']
    remaining=product.quantity-total_ordered
    context={
        'product':product,
        'orders':orders,
        'total_ordered':total_ordered,
        'remaining':remaining,
    }
    return render(request,'dashboard/product_orders.html',context)




from django.http import JsonResponse

@login_required
def product_autocomplete(request):
    if 'term' in request.GET:
        qs = Products.objects.filter(name__icontains=request.GET.get('term'))
        # Send both label (name) and value (id)
        data = [{'label': p.name, 'value': p.id} for p in qs]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


@login_required
def product_audit(request, pk):
    product = Products.objects.get(id=pk)
    context = {'product': product}
    return render(request, 'dashboard/product_audit.html', context)



stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_checkout_session(request, pk):
    product = get_object_or_404(Products, id=pk)
    YOUR_DOMAIN = "http://127.0.0.1:8000"

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': product.name},
                    'unit_amount': int(product.price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success/',
            cancel_url=YOUR_DOMAIN + '/cancel/',
        )
        return JsonResponse({'id': checkout_session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)})





from django.utils import timezone

def order_success(request, product_id, quantity):
    product = Products.objects.get(id=product_id)
    quantity = int(quantity)

    if product.quantity >= quantity:
        product.quantity -= quantity
        product.save()

        # Calculate payment amount based on product price
        payment_amount = product.price * quantity  # Make sure 'price' exists in Products model

        # Create order and save payment info
        Order.objects.create(
            staff=request.user,
            products=product,
            order_quantity=quantity,
            payment_amount=payment_amount,
            payment_date=timezone.now()
        )

        messages.success(request, "Payment successful and order placed!")
    else:
        messages.error(request, "Stock not available after payment.")

    return redirect('dashboard-index')







def upload_products(request):
    if request.method == "POST":
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            wb = openpyxl.load_workbook(file)
            sheet = wb.active

            errors = []

            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row or len(row) < 4:
                    continue  # skip empty or incomplete rows

                product_name, category, quantity, price = row[:4]

                # Skip rows where required fields are missing
                if not product_name or not category or quantity is None or price is None:
                    errors.append(f"Skipped row due to missing data: {row}")
                    continue

                # Ensure quantity and price are numbers
                try:
                    quantity = int(quantity)
                    price = float(price)
                except ValueError:
                    errors.append(f"Skipped row due to invalid number: {row}")
                    continue

                product, created = Products.objects.get_or_create(
                    name=product_name,
                    defaults={
                        "category": category,
                        "quantity": 0,
                        "price": price,
                    }
                )
                if not created:
                    product.quantity +=quantity
                    product.price =price
                product.save()

                if created:
                    print(f"New product added: {product_name}")
                else:
                    print(f"Updated product: {product_name}")

            if errors:
                messages.warning(request, "Some rows were skipped:\n" + "\n".join(errors))

            messages.success(request, "Products imported/updated successfully!")
            return redirect('dashboard-product')  # Change to your product list view name
    else:
        form = UploadExcelForm()

    return render(request, "dashboard/upload_products.html", {"form": form})

