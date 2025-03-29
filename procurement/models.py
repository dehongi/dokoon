from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings
from accounts.models import CustomUser
from shop.models import Product, ProductVariation
from inventory.models import Supplier, Warehouse, PurchaseOrder


class VendorCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Vendor Categories"

    def __str__(self):
        return self.name


class Vendor(models.Model):
    VENDOR_TYPES = (
        ("manufacturer", "Manufacturer"),
        ("distributor", "Distributor"),
        ("wholesaler", "Wholesaler"),
        ("retailer", "Retailer"),
        ("service", "Service Provider"),
    )

    VENDOR_STATUS = (
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("on_hold", "On Hold"),
        ("blacklisted", "Blacklisted"),
        ("pending_approval", "Pending Approval"),
    )

    # Link to the inventory supplier
    supplier = models.OneToOneField(
        Supplier, on_delete=models.CASCADE, related_name="vendor_profile"
    )
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPES)
    categories = models.ManyToManyField(
        VendorCategory, blank=True, related_name="vendors"
    )
    status = models.CharField(max_length=20, choices=VENDOR_STATUS, default="active")

    # Financial and business information
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    credit_terms = models.CharField(max_length=100, blank=True, null=True)
    credit_limit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    # Performance metrics
    quality_rating = models.PositiveSmallIntegerField(
        blank=True, null=True, help_text="Rating from 1-10"
    )
    delivery_rating = models.PositiveSmallIntegerField(
        blank=True, null=True, help_text="Rating from 1-10"
    )
    price_rating = models.PositiveSmallIntegerField(
        blank=True, null=True, help_text="Rating from 1-10"
    )

    # Additional information
    certifications = models.TextField(
        blank=True, null=True, help_text="List any vendor certifications"
    )
    onboarding_date = models.DateField(blank=True, null=True)
    last_review_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.supplier.name

    @property
    def overall_rating(self):
        ratings = [
            r
            for r in [self.quality_rating, self.delivery_rating, self.price_rating]
            if r is not None
        ]
        if not ratings:
            return None
        return sum(ratings) / len(ratings)


class VendorContact(models.Model):
    CONTACT_TYPES = (
        ("primary", "Primary"),
        ("billing", "Billing"),
        ("shipping", "Shipping"),
        ("sales", "Sales"),
        ("technical", "Technical"),
        ("customer_service", "Customer Service"),
        ("other", "Other"),
    )

    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="contacts"
    )
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES)
    name = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, null=True)
    mobile = models.CharField(max_length=30, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.vendor.supplier.name} - {self.get_contact_type_display()})"

    def save(self, *args, **kwargs):
        # If this contact is marked as primary, unmark other primary contacts
        if self.is_primary:
            VendorContact.objects.filter(vendor=self.vendor, is_primary=True).exclude(
                id=self.id
            ).update(is_primary=False)
        super().save(*args, **kwargs)


class VendorProduct(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="products"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="vendor_products"
    )
    variation = models.ForeignKey(
        ProductVariation,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="vendor_products",
    )
    vendor_product_code = models.CharField(max_length=100, blank=True, null=True)
    vendor_product_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The vendor's name for this product",
    )
    standard_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    minimum_order_quantity = models.PositiveIntegerField(default=1)
    lead_time_days = models.PositiveIntegerField(blank=True, null=True)
    is_preferred_vendor = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    last_purchase_date = models.DateField(blank=True, null=True)
    last_purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("vendor", "product", "variation")

    def __str__(self):
        base = f"{self.product.name}"
        if self.variation:
            base += f" - {self.variation.name}: {self.variation.value}"
        return f"{base} ({self.vendor.supplier.name})"

    def save(self, *args, **kwargs):
        # If this vendor is marked preferred, unmark others for this product+variation combo
        if self.is_preferred_vendor:
            VendorProduct.objects.filter(
                product=self.product, variation=self.variation, is_preferred_vendor=True
            ).exclude(id=self.id).update(is_preferred_vendor=False)
        super().save(*args, **kwargs)


class VendorPriceList(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="price_lists"
    )
    name = models.CharField(max_length=100)
    effective_date = models.DateField()
    expiration_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="procurement/price_lists/", blank=True, null=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_price_lists",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_date"]

    def __str__(self):
        return f"{self.vendor.supplier.name} - {self.name} ({self.effective_date})"

    @property
    def is_expired(self):
        return self.expiration_date and self.expiration_date < timezone.now().date()


class VendorPriceListItem(models.Model):
    price_list = models.ForeignKey(
        VendorPriceList, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ForeignKey(
        ProductVariation, on_delete=models.SET_NULL, blank=True, null=True
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    minimum_order_quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("price_list", "product", "variation")

    def __str__(self):
        base = f"{self.product.name}"
        if self.variation:
            base += f" - {self.variation.name}: {self.variation.value}"
        return f"{base} - {self.price}"


class PurchaseRequisition(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("pending_approval", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("converted", "Converted to PO"),
        ("cancelled", "Cancelled"),
    )

    requisition_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    requester = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="purchase_requisitions"
    )
    department = models.CharField(max_length=100, blank=True, null=True)
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="purchase_requisitions"
    )
    date_required = models.DateField()
    justification = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Approval information
    approver = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_requisitions",
    )
    approval_date = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    total_estimated_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PR-{self.requisition_number} ({self.get_status_display()})"


class PurchaseRequisitionItem(models.Model):
    requisition = models.ForeignKey(
        PurchaseRequisition, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ForeignKey(
        ProductVariation, on_delete=models.SET_NULL, blank=True, null=True
    )
    quantity = models.PositiveIntegerField()
    estimated_unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    suggested_vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="suggested_items",
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("requisition", "product", "variation")

    def __str__(self):
        base = f"{self.product.name}"
        if self.variation:
            base += f" - {self.variation.name}: {self.variation.value}"
        return f"{base} ({self.quantity})"

    @property
    def subtotal(self):
        return self.quantity * self.estimated_unit_price


class RFQ(models.Model):
    """Request for Quotation"""

    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("sent", "Sent to Vendors"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    rfq_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    requisition = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="rfqs",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Dates
    issue_date = models.DateField(default=timezone.now)
    response_deadline = models.DateField()
    expected_delivery_date = models.DateField(blank=True, null=True)

    # Who's responsible
    requester = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="requested_rfqs"
    )
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="assigned_rfqs",
    )

    notes = models.TextField(blank=True, null=True)
    terms_and_conditions = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "RFQ"
        verbose_name_plural = "RFQs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"RFQ-{self.rfq_number} ({self.title})"


class RFQItem(models.Model):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ForeignKey(
        ProductVariation, on_delete=models.SET_NULL, blank=True, null=True
    )
    quantity = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)

    # From requisition item if applicable
    requisition_item = models.ForeignKey(
        PurchaseRequisitionItem,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="rfq_items",
    )

    class Meta:
        unique_together = ("rfq", "product", "variation")

    def __str__(self):
        base = f"{self.product.name}"
        if self.variation:
            base += f" - {self.variation.name}: {self.variation.value}"
        return f"{base} ({self.quantity})"


class RFQVendor(models.Model):
    STATUS_CHOICES = (
        ("invited", "Invited"),
        ("acknowledged", "Acknowledged"),
        ("declined", "Declined"),
        ("quote_submitted", "Quote Submitted"),
        ("selected", "Selected"),
        ("rejected", "Rejected"),
    )

    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="vendors")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="rfqs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="invited")

    # Communication details
    date_invited = models.DateField(default=timezone.now)
    date_acknowledged = models.DateField(blank=True, null=True)
    date_quote_received = models.DateField(blank=True, null=True)

    contact = models.ForeignKey(
        VendorContact,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="rfqs",
    )
    notes = models.TextField(blank=True, null=True)

    # Quote details
    quote_reference = models.CharField(max_length=100, blank=True, null=True)
    total_quoted_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    quoted_lead_time_days = models.PositiveIntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("rfq", "vendor")

    def __str__(self):
        return f"{self.rfq.rfq_number} - {self.vendor.supplier.name} ({self.get_status_display()})"


class RFQVendorItem(models.Model):
    rfq_vendor = models.ForeignKey(
        RFQVendor, on_delete=models.CASCADE, related_name="items"
    )
    rfq_item = models.ForeignKey(
        RFQItem, on_delete=models.CASCADE, related_name="vendor_quotes"
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    lead_time_days = models.PositiveIntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_selected = models.BooleanField(default=False)

    class Meta:
        unique_together = ("rfq_vendor", "rfq_item")

    def __str__(self):
        item = self.rfq_item
        base = f"{item.product.name}"
        if item.variation:
            base += f" - {item.variation.name}: {item.variation.value}"
        return f"{base} - {self.unit_price} ({self.rfq_vendor.vendor.supplier.name})"

    @property
    def subtotal(self):
        return self.unit_price * self.rfq_item.quantity


class ProcurementAttachment(models.Model):
    """Generic model for attachments to various procurement entities"""

    ATTACHMENT_TYPES = (
        ("document", "Document"),
        ("image", "Image"),
        ("contract", "Contract"),
        ("quote", "Quote"),
        ("specification", "Specification"),
        ("other", "Other"),
    )

    # Polymorphic relationships to various entities
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="attachments",
    )
    requisition = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="attachments",
    )
    rfq = models.ForeignKey(
        RFQ, on_delete=models.CASCADE, blank=True, null=True, related_name="attachments"
    )
    rfq_vendor = models.ForeignKey(
        RFQVendor,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="attachments",
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="attachments",
    )

    name = models.CharField(max_length=255)
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES)
    file = models.FileField(upload_to="procurement/attachments/")
    description = models.TextField(blank=True, null=True)

    uploaded_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="uploaded_attachments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class VendorPerformance(models.Model):
    """Track vendor performance metrics over time"""

    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="performance_records"
    )
    evaluation_date = models.DateField()
    evaluator = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="vendor_evaluations",
    )

    # Ratings (1-10)
    quality_rating = models.PositiveSmallIntegerField(help_text="Rating from 1-10")
    delivery_rating = models.PositiveSmallIntegerField(help_text="Rating from 1-10")
    price_rating = models.PositiveSmallIntegerField(help_text="Rating from 1-10")
    service_rating = models.PositiveSmallIntegerField(help_text="Rating from 1-10")

    # Performance metrics
    on_time_delivery_rate = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, help_text="Percentage"
    )
    quality_rejection_rate = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, help_text="Percentage"
    )
    response_time_days = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )

    # Evaluation details
    comments = models.TextField(blank=True, null=True)
    areas_of_improvement = models.TextField(blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-evaluation_date"]

    def __str__(self):
        return f"{self.vendor.supplier.name} Evaluation - {self.evaluation_date}"

    @property
    def overall_rating(self):
        return (
            self.quality_rating
            + self.delivery_rating
            + self.price_rating
            + self.service_rating
        ) / 4
