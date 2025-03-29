from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # Warehouse URLs
    path("warehouses/", views.warehouse_list, name="warehouse_list"),
    path("warehouses/<int:pk>/", views.warehouse_detail, name="warehouse_detail"),
    # Stock item URLs
    path("stock/<int:pk>/", views.stock_item_detail, name="stock_item_detail"),
    path(
        "stock/<int:stock_id>/add-transaction/",
        views.add_stock_transaction,
        name="add_stock_transaction",
    ),
    # Supplier URLs
    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers/<int:pk>/", views.supplier_detail, name="supplier_detail"),
    # Purchase order URLs
    path("purchase-orders/", views.purchase_order_list, name="purchase_order_list"),
    path(
        "purchase-orders/<int:pk>/",
        views.purchase_order_detail,
        name="purchase_order_detail",
    ),
    # Inventory transfer URLs
    path("transfers/", views.inventory_transfer_list, name="transfer_list"),
    path(
        "transfers/<int:pk>/", views.inventory_transfer_detail, name="transfer_detail"
    ),
    # API endpoints
    path("api/product-stock/", views.product_stock_api, name="product_stock_api"),
]
