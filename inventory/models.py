from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from shop.models import Product, ProductVariation
from accounts.models import CustomUser


class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def total_inventory_value(self):
        return sum(stock.total_value for stock in self.stock_items.all())

    @property
    def total_stock_items(self):
        return self.stock_items.count()


class StockItem(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="stock_items"
    )
    variation = models.ForeignKey(
        ProductVariation,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="stock_items",
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="stock_items"
    )
    quantity = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(default=5)
    max_stock_level = models.PositiveIntegerField(default=100)
    cost_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    location_code = models.CharField(
        max_length=50, help_text="Shelf/Bin location code", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("product", "variation", "warehouse")

    def __str__(self):
        base = f"{self.product.name}"
        if self.variation:
            base += f" - {self.variation.name}: {self.variation.value}"
        return f"{base} at {self.warehouse.name} ({self.quantity} units)"

    @property
    def total_value(self):
        return self.quantity * self.cost_per_unit

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level

    @property
    def is_over_stock(self):
        return self.quantity >= self.max_stock_level


class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = (
        ("purchase", "Purchase"),
        ("sale", "Sale"),
        ("adjustment", "Adjustment"),
        ("transfer", "Transfer"),
        ("return", "Return"),
        ("write_off", "Write Off"),
    )

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField(
        help_text="Positive for additions, negative for removals"
    )
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    reference_number = models.CharField(
        max_length=100, blank=True, null=True, help_text="Order/Invoice reference"
    )
    performed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="inventory_transactions",
    )
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.stock_item.product.name} - {self.quantity} units"


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    payment_terms = models.CharField(max_length=100, blank=True, null=True)
    lead_time_days = models.PositiveIntegerField(
        blank=True, null=True, help_text="Average lead time in days"
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("ordered", "Ordered"),
        ("partial", "Partially Received"),
        ("received", "Received"),
        ("cancelled", "Cancelled"),
    )

    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name="purchase_orders"
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="purchase_orders"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField(blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_purchase_orders",
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="approved_purchase_orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PO-{self.order_number} ({self.supplier.name})"

    @property
    def total_with_tax_shipping(self):
        return self.total_amount + self.tax_amount + self.shipping_cost

    @property
    def items_count(self):
        return self.items.count()


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ForeignKey(
        ProductVariation, on_delete=models.SET_NULL, blank=True, null=True
    )
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("purchase_order", "product", "variation")

    def __str__(self):
        base = f"{self.product.name}"
        if self.variation:
            base += f" - {self.variation.name}: {self.variation.value}"
        return f"{base} ({self.quantity_ordered} units)"

    @property
    def subtotal(self):
        return self.quantity_ordered * self.unit_cost

    @property
    def is_fully_received(self):
        return self.quantity_received >= self.quantity_ordered


class InventoryAdjustment(models.Model):
    ADJUSTMENT_TYPES = (
        ("count", "Physical Count"),
        ("damage", "Damage/Loss"),
        ("expiry", "Expiration"),
        ("theft", "Theft"),
        ("error", "Error Correction"),
        ("other", "Other"),
    )

    adjustment_number = models.CharField(max_length=50, unique=True)
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="inventory_adjustments"
    )
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="inventory_adjustments",
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="approved_adjustments",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adjustment #{self.adjustment_number} - {self.get_adjustment_type_display()}"


class InventoryAdjustmentItem(models.Model):
    adjustment = models.ForeignKey(
        InventoryAdjustment, on_delete=models.CASCADE, related_name="items"
    )
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE)
    previous_quantity = models.PositiveIntegerField()
    new_quantity = models.PositiveIntegerField()
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        product_name = self.stock_item.product.name
        return f"{product_name} - adjusted from {self.previous_quantity} to {self.new_quantity}"

    @property
    def quantity_change(self):
        return self.new_quantity - self.previous_quantity


class InventoryTransfer(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("pending", "Pending"),
        ("in_transit", "In Transit"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    transfer_number = models.CharField(max_length=50, unique=True)
    source_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="outgoing_transfers"
    )
    destination_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="incoming_transfers"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    shipping_date = models.DateField(blank=True, null=True)
    expected_arrival_date = models.DateField(blank=True, null=True)
    arrival_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_transfers",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transfer #{self.transfer_number} - {self.source_warehouse.name} to {self.destination_warehouse.name}"

    @property
    def is_same_warehouse(self):
        return self.source_warehouse == self.destination_warehouse


class InventoryTransferItem(models.Model):
    transfer = models.ForeignKey(
        InventoryTransfer, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ForeignKey(
        ProductVariation, on_delete=models.SET_NULL, blank=True, null=True
    )
    quantity = models.PositiveIntegerField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"
