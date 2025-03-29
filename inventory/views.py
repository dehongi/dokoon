from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from .models import (
    Warehouse,
    StockItem,
    InventoryTransaction,
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    InventoryAdjustment,
    InventoryAdjustmentItem,
    InventoryTransfer,
    InventoryTransferItem,
)
from shop.models import Product


@login_required
def dashboard(request):
    # Get inventory summary data
    total_products = Product.objects.filter(is_active=True).count()
    total_stock_value = (
        StockItem.objects.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("quantity") * F("cost_per_unit"), output_field=DecimalField()
                )
            )
        )["total"]
        or 0
    )

    low_stock_items = StockItem.objects.filter(
        quantity__lte=F("min_stock_level")
    ).count()

    # Recent transactions
    recent_transactions = InventoryTransaction.objects.all().order_by("-timestamp")[:10]

    # Upcoming purchase orders
    upcoming_orders = PurchaseOrder.objects.filter(
        status__in=["pending", "approved", "ordered"],
        expected_delivery_date__gte=timezone.now().date(),
    ).order_by("expected_delivery_date")[:5]

    context = {
        "total_products": total_products,
        "total_stock_value": total_stock_value,
        "low_stock_items": low_stock_items,
        "recent_transactions": recent_transactions,
        "upcoming_orders": upcoming_orders,
    }

    return render(request, "inventory/dashboard.html", context)


@login_required
def warehouse_list(request):
    warehouses = Warehouse.objects.all()

    context = {
        "warehouses": warehouses,
    }

    return render(request, "inventory/warehouse_list.html", context)


@login_required
def warehouse_detail(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    stock_items = warehouse.stock_items.all().select_related("product", "variation")

    # Filter options
    filter_by = request.GET.get("filter")
    if filter_by == "low_stock":
        stock_items = stock_items.filter(quantity__lte=F("min_stock_level"))
    elif filter_by == "out_of_stock":
        stock_items = stock_items.filter(quantity=0)

    # Search functionality
    query = request.GET.get("q")
    if query:
        stock_items = stock_items.filter(
            Q(product__name__icontains=query)
            | Q(product__sku__icontains=query)
            | Q(location_code__icontains=query)
        )

    context = {
        "warehouse": warehouse,
        "stock_items": stock_items,
        "filter_by": filter_by,
        "query": query,
    }

    return render(request, "inventory/warehouse_detail.html", context)


@login_required
def stock_item_detail(request, pk):
    stock_item = get_object_or_404(StockItem, pk=pk)
    transactions = stock_item.transactions.all().order_by("-timestamp")

    context = {
        "stock_item": stock_item,
        "transactions": transactions,
    }

    return render(request, "inventory/stock_item_detail.html", context)


@login_required
@permission_required("inventory.add_inventorytransaction")
def add_stock_transaction(request, stock_id):
    stock_item = get_object_or_404(StockItem, pk=stock_id)

    if request.method == "POST":
        transaction_type = request.POST.get("transaction_type")
        quantity = int(request.POST.get("quantity", 0))
        unit_cost = float(request.POST.get("unit_cost") or stock_item.cost_per_unit)
        reference = request.POST.get("reference")
        notes = request.POST.get("notes", "")

        # Create the transaction
        transaction = InventoryTransaction.objects.create(
            stock_item=stock_item,
            transaction_type=transaction_type,
            quantity=quantity,
            unit_cost=unit_cost,
            reference_number=reference,
            notes=notes,
            performed_by=request.user,
        )

        # Update the stock quantity
        stock_item.quantity += quantity
        if stock_item.quantity < 0:
            stock_item.quantity = 0
        stock_item.save()

        messages.success(request, "Transaction added successfully")
        return redirect("inventory:stock_item_detail", pk=stock_item.pk)

    context = {
        "stock_item": stock_item,
    }

    return render(request, "inventory/add_transaction.html", context)


@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()

    context = {
        "suppliers": suppliers,
    }

    return render(request, "inventory/supplier_list.html", context)


@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    purchase_orders = supplier.purchase_orders.all().order_by("-order_date")

    context = {
        "supplier": supplier,
        "purchase_orders": purchase_orders,
    }

    return render(request, "inventory/supplier_detail.html", context)


@login_required
def purchase_order_list(request):
    status_filter = request.GET.get("status")

    if status_filter:
        purchase_orders = PurchaseOrder.objects.filter(status=status_filter)
    else:
        purchase_orders = PurchaseOrder.objects.all()

    purchase_orders = purchase_orders.order_by("-order_date")

    context = {
        "purchase_orders": purchase_orders,
        "status_filter": status_filter,
    }

    return render(request, "inventory/purchase_order_list.html", context)


@login_required
def purchase_order_detail(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)

    context = {
        "purchase_order": purchase_order,
    }

    return render(request, "inventory/purchase_order_detail.html", context)


@login_required
def inventory_transfer_list(request):
    status_filter = request.GET.get("status")

    if status_filter:
        transfers = InventoryTransfer.objects.filter(status=status_filter)
    else:
        transfers = InventoryTransfer.objects.all()

    transfers = transfers.order_by("-shipping_date")

    context = {
        "transfers": transfers,
        "status_filter": status_filter,
    }

    return render(request, "inventory/transfer_list.html", context)


@login_required
def inventory_transfer_detail(request, pk):
    transfer = get_object_or_404(InventoryTransfer, pk=pk)

    context = {
        "transfer": transfer,
    }

    return render(request, "inventory/transfer_detail.html", context)


# API endpoint to check product stock across all warehouses
@login_required
def product_stock_api(request):
    product_id = request.GET.get("product_id")

    if not product_id:
        return JsonResponse({"error": "Product ID is required"}, status=400)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    stock_items = StockItem.objects.filter(product=product).select_related("warehouse")

    result = {
        "product": {"id": product.id, "name": product.name, "sku": product.sku},
        "stock": [],
    }

    for item in stock_items:
        result["stock"].append(
            {
                "warehouse_id": item.warehouse.id,
                "warehouse_name": item.warehouse.name,
                "quantity": item.quantity,
                "location_code": item.location_code,
                "is_low_stock": item.is_low_stock,
            }
        )

    return JsonResponse(result)
