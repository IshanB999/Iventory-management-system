from django.urls import path
from . import views


urlpatterns=[
    path('',views.index,name='dashboard-index'),
    path('dashboard/',views.index,name='dashboard-index'),
    path('staff/',views.staff,name='dashboard-staff'),
    path('staff/detail/<int:pk>',views.staff_detail,name='dashboard-staff-detail'),
    path('product/',views.product,name='dashboard-product'),
    path('product/delete/<int:pk>/',views.product_delete,name='dashboard-product-delete'),
    path('product/update/<int:pk>/',views.product_update,name='dashboard-product-update'),
    path('order/',views.order_list,name='dashboard-order'),
    path('product/<int:pk>/orders/',views.product_orders,name='product-orders'),
    path('product/<int:pk>/audit/', views.product_audit, name='product-audit'),
    path('product-autocomplete/', views.product_autocomplete, name='product-autocomplete'),
    path('checkout/<int:pk>/', views.create_checkout_session, name='checkout'),
    path('dashboard/order-success/<int:product_id>/<int:quantity>/', views.order_success, name='order-success'),

    

]