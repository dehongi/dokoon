from django.urls import path
from . import views

app_name = "procurement"

urlpatterns = [
    # Dashboard
    path("", views.procurement_dashboard, name="dashboard"),
    # Vendor URLs
    path("vendors/", views.vendor_list, name="vendor_list"),
    path("vendors/<int:pk>/", views.vendor_detail, name="vendor_detail"),
    # Purchase Requisition URLs
    path("requisitions/", views.requisition_list, name="requisition_list"),
    path("requisitions/<int:pk>/", views.requisition_detail, name="requisition_detail"),
    # RFQ URLs
    path("rfqs/", views.rfq_list, name="rfq_list"),
    path("rfqs/<int:pk>/", views.rfq_detail, name="rfq_detail"),
    path("rfqs/vendor/<int:pk>/", views.rfq_vendor_detail, name="rfq_vendor_detail"),
    # API Endpoints
    path(
        "api/vendors/<int:vendor_id>/products/",
        views.get_vendor_products,
        name="get_vendor_products",
    ),
    path(
        "api/products/<int:product_id>/vendors/",
        views.get_vendors_for_product,
        name="get_vendors_for_product",
    ),
]
