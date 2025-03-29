from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Sum, F, Count
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse

from .models import (
    VendorCategory,
    Vendor,
    VendorContact,
    VendorProduct,
    VendorPriceList,
    VendorPriceListItem,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    RFQ,
    RFQItem,
    RFQVendor,
    RFQVendorItem,
    ProcurementAttachment,
    VendorPerformance,
)
from inventory.models import Supplier, Warehouse


@login_required
def procurement_dashboard(request):
    """Main dashboard for procurement app."""
    # Get stats for the dashboard
    active_vendors = Vendor.objects.filter(status="active").count()
    pending_requisitions = PurchaseRequisition.objects.filter(
        status="pending_approval"
    ).count()
    open_rfqs = RFQ.objects.filter(status__in=["draft", "sent", "in_progress"]).count()

    # Recently added vendors
    recent_vendors = Vendor.objects.all().order_by("-created_at")[:5]

    # Recent purchase requisitions
    recent_requisitions = PurchaseRequisition.objects.all().order_by("-created_at")[:5]

    # Active RFQs
    active_rfqs = RFQ.objects.filter(status__in=["sent", "in_progress"]).order_by(
        "-response_deadline"
    )[:5]

    context = {
        "active_vendors": active_vendors,
        "pending_requisitions": pending_requisitions,
        "open_rfqs": open_rfqs,
        "recent_vendors": recent_vendors,
        "recent_requisitions": recent_requisitions,
        "active_rfqs": active_rfqs,
    }

    return render(request, "procurement/dashboard.html", context)


# Vendor Views
@login_required
def vendor_list(request):
    """List all vendors with filtering options."""
    vendors = Vendor.objects.all()

    # Filter by status
    status_filter = request.GET.get("status")
    if status_filter:
        vendors = vendors.filter(status=status_filter)

    # Filter by type
    type_filter = request.GET.get("type")
    if type_filter:
        vendors = vendors.filter(vendor_type=type_filter)

    # Filter by category
    category_filter = request.GET.get("category")
    if category_filter:
        vendors = vendors.filter(categories__id=category_filter)

    # Search functionality
    search_query = request.GET.get("q")
    if search_query:
        vendors = vendors.filter(
            Q(supplier__name__icontains=search_query)
            | Q(supplier__code__icontains=search_query)
            | Q(tax_id__icontains=search_query)
        )

    # Get categories for the filter dropdown
    categories = VendorCategory.objects.all()

    context = {
        "vendors": vendors,
        "categories": categories,
        "status_filter": status_filter,
        "type_filter": type_filter,
        "category_filter": category_filter,
        "search_query": search_query,
    }

    return render(request, "procurement/vendor_list.html", context)


@login_required
def vendor_detail(request, pk):
    """Display detailed information about a vendor."""
    vendor = get_object_or_404(Vendor, pk=pk)

    # Get related data
    contacts = vendor.contacts.all()
    products = vendor.products.all()
    price_lists = vendor.price_lists.all().order_by("-effective_date")
    performance_records = vendor.performance_records.all().order_by("-evaluation_date")
    attachments = vendor.attachments.all()

    context = {
        "vendor": vendor,
        "contacts": contacts,
        "products": products,
        "price_lists": price_lists,
        "performance_records": performance_records,
        "attachments": attachments,
    }

    return render(request, "procurement/vendor_detail.html", context)


# Purchase Requisition Views
@login_required
def requisition_list(request):
    """List all purchase requisitions with filtering options."""
    # Default to showing requisitions created by the current user
    requisitions = PurchaseRequisition.objects.all()

    # Filter by status
    status_filter = request.GET.get("status")
    if status_filter:
        requisitions = requisitions.filter(status=status_filter)

    # Filter by warehouse
    warehouse_filter = request.GET.get("warehouse")
    if warehouse_filter:
        requisitions = requisitions.filter(warehouse__id=warehouse_filter)

    # Filter by date range
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    if date_from:
        requisitions = requisitions.filter(created_at__gte=date_from)
    if date_to:
        requisitions = requisitions.filter(created_at__lte=date_to)

    # Search functionality
    search_query = request.GET.get("q")
    if search_query:
        requisitions = requisitions.filter(
            Q(requisition_number__icontains=search_query)
            | Q(requester__email__icontains=search_query)
            | Q(department__icontains=search_query)
            | Q(notes__icontains=search_query)
        )

    # Get warehouses for the filter dropdown
    warehouses = Warehouse.objects.all()

    context = {
        "requisitions": requisitions.order_by("-created_at"),
        "warehouses": warehouses,
        "status_filter": status_filter,
        "warehouse_filter": warehouse_filter,
        "date_from": date_from,
        "date_to": date_to,
        "search_query": search_query,
    }

    return render(request, "procurement/requisition_list.html", context)


@login_required
def requisition_detail(request, pk):
    """Display detailed information about a purchase requisition."""
    requisition = get_object_or_404(PurchaseRequisition, pk=pk)

    # Get related data
    items = requisition.items.all()
    attachments = requisition.attachments.all()
    rfqs = requisition.rfqs.all()

    context = {
        "requisition": requisition,
        "items": items,
        "attachments": attachments,
        "rfqs": rfqs,
    }

    return render(request, "procurement/requisition_detail.html", context)


# RFQ Views
@login_required
def rfq_list(request):
    """List all RFQs with filtering options."""
    rfqs = RFQ.objects.all()

    # Filter by status
    status_filter = request.GET.get("status")
    if status_filter:
        rfqs = rfqs.filter(status=status_filter)

    # Filter by requester
    if request.GET.get("my_rfqs"):
        rfqs = rfqs.filter(requester=request.user)

    # Filter by assignee
    if request.GET.get("assigned_to_me"):
        rfqs = rfqs.filter(assigned_to=request.user)

    # Filter by date range
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    if date_from:
        rfqs = rfqs.filter(issue_date__gte=date_from)
    if date_to:
        rfqs = rfqs.filter(issue_date__lte=date_to)

    # Search functionality
    search_query = request.GET.get("q")
    if search_query:
        rfqs = rfqs.filter(
            Q(rfq_number__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    context = {
        "rfqs": rfqs.order_by("-created_at"),
        "status_filter": status_filter,
        "date_from": date_from,
        "date_to": date_to,
        "search_query": search_query,
    }

    return render(request, "procurement/rfq_list.html", context)


@login_required
def rfq_detail(request, pk):
    """Display detailed information about an RFQ."""
    rfq = get_object_or_404(RFQ, pk=pk)

    # Get related data
    items = rfq.items.all()
    vendors = rfq.vendors.all()
    attachments = rfq.attachments.all()

    context = {
        "rfq": rfq,
        "items": items,
        "vendors": vendors,
        "attachments": attachments,
    }

    return render(request, "procurement/rfq_detail.html", context)


@login_required
def rfq_vendor_detail(request, pk):
    """Display detailed information about an RFQ vendor quote."""
    rfq_vendor = get_object_or_404(RFQVendor, pk=pk)

    # Get related data
    items = rfq_vendor.items.all()
    attachments = rfq_vendor.attachments.all()

    context = {
        "rfq_vendor": rfq_vendor,
        "items": items,
        "attachments": attachments,
    }

    return render(request, "procurement/rfq_vendor_detail.html", context)


# API Endpoints
@login_required
def get_vendor_products(request, vendor_id):
    """API endpoint to get products offered by a specific vendor."""
    try:
        vendor = Vendor.objects.get(id=vendor_id)
        products = VendorProduct.objects.filter(vendor=vendor)

        data = []
        for product in products:
            product_data = {
                "id": product.id,
                "product_id": product.product.id,
                "product_name": product.product.name,
                "sku": product.product.sku,
                "price": float(product.standard_price),
                "minimum_order_quantity": product.minimum_order_quantity,
                "lead_time_days": product.lead_time_days or 0,
            }

            if product.variation:
                product_data["variation_id"] = product.variation.id
                product_data["variation_name"] = (
                    f"{product.variation.name}: {product.variation.value}"
                )

            data.append(product_data)

        return JsonResponse({"success": True, "products": data})

    except Vendor.DoesNotExist:
        return JsonResponse({"success": False, "error": "Vendor not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def get_vendors_for_product(request, product_id):
    """API endpoint to get vendors who can supply a specific product."""
    try:
        vendors = VendorProduct.objects.filter(
            product_id=product_id, vendor__status="active"
        ).select_related("vendor", "vendor__supplier")

        data = []
        for vendor_product in vendors:
            vendor = vendor_product.vendor
            data.append(
                {
                    "vendor_id": vendor.id,
                    "vendor_name": vendor.supplier.name,
                    "standard_price": float(vendor_product.standard_price),
                    "lead_time_days": vendor_product.lead_time_days or 0,
                    "minimum_order_quantity": vendor_product.minimum_order_quantity,
                    "is_preferred": vendor_product.is_preferred_vendor,
                }
            )

        return JsonResponse({"success": True, "vendors": data})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
