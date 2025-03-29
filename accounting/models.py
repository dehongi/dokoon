from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings
from accounts.models import CustomUser
from shop.models import Order
from inventory.models import PurchaseOrder, Supplier
from procurement.models import Vendor


class FiscalYear(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one active fiscal year
        if self.is_active:
            FiscalYear.objects.filter(is_active=True).exclude(id=self.id).update(
                is_active=False
            )
        super().save(*args, **kwargs)


class AccountType(models.Model):
    TYPE_CHOICES = (
        ("asset", "Asset"),
        ("liability", "Liability"),
        ("equity", "Equity"),
        ("revenue", "Revenue"),
        ("expense", "Expense"),
    )

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Account(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    account_type = models.ForeignKey(
        AccountType, on_delete=models.PROTECT, related_name="accounts"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True, related_name="children"
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Balance fields (calculated and cached)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def is_debit_balance(self):
        """
        Determine if the account normally has a debit balance.
        Asset and Expense accounts normally have debit balances.
        """
        return self.account_type.type in ["asset", "expense"]

    @property
    def has_children(self):
        return self.children.exists()


class Journal(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("posted", "Posted"),
        ("cancelled", "Cancelled"),
    )

    journal = models.ForeignKey(
        Journal, on_delete=models.PROTECT, related_name="entries"
    )
    fiscal_year = models.ForeignKey(
        FiscalYear, on_delete=models.PROTECT, related_name="journal_entries"
    )
    entry_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Optional relations to other system entities for reference
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="journal_entries",
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="journal_entries",
    )

    # Audit fields
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_journal_entries",
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_journal_entries",
    )
    posted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-entry_number"]
        verbose_name_plural = "Journal Entries"

    def __str__(self):
        return f"{self.entry_number} - {self.date}"

    @property
    def is_balanced(self):
        """Check if debits equal credits"""
        total_debits = sum(line.debit_amount for line in self.lines.all())
        total_credits = sum(line.credit_amount for line in self.lines.all())
        return total_debits == total_credits

    @property
    def total_amount(self):
        """Return the total amount of the journal entry (sum of debits or credits)"""
        return sum(line.debit_amount for line in self.lines.all())

    def post(self, user):
        """Post the journal entry, updating account balances"""
        if self.status != "draft":
            raise ValueError("Only draft journal entries can be posted")

        if not self.is_balanced:
            raise ValueError("Journal entry must be balanced before posting")

        # Update account balances
        for line in self.lines.all():
            account = line.account

            # Adjust balance based on debit/credit and account type
            if line.debit_amount > 0:
                if account.is_debit_balance:
                    account.current_balance += line.debit_amount
                else:
                    account.current_balance -= line.debit_amount

            if line.credit_amount > 0:
                if account.is_debit_balance:
                    account.current_balance -= line.credit_amount
                else:
                    account.current_balance += line.credit_amount

            account.save()

        # Update journal entry status and metadata
        self.status = "posted"
        self.approved_by = user
        self.posted_at = timezone.now()
        self.save()


class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.CASCADE, related_name="lines"
    )
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="journal_lines"
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    debit_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    credit_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    # Optional reference fields for detailed record keeping
    reference = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        if self.debit_amount > 0:
            return f"{self.account.name} - Dr. {self.debit_amount}"
        return f"{self.account.name} - Cr. {self.credit_amount}"

    def clean(self):
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValueError(
                "A journal entry line cannot have both debit and credit amounts"
            )
        if self.debit_amount == 0 and self.credit_amount == 0:
            raise ValueError(
                "A journal entry line must have either a debit or credit amount"
            )


class Vendor(models.Model):
    """Extends the Procurement Vendor model with accounting-specific information"""

    procurement_vendor = models.OneToOneField(
        Vendor, on_delete=models.CASCADE, related_name="accounting"
    )

    # Accounts assigned to this vendor
    payable_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="vendor_payables"
    )
    expense_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="vendor_expenses",
        blank=True,
        null=True,
    )

    # Accounting metrics
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ytd_purchases = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"Accounting for {self.procurement_vendor.supplier.name}"


class Customer(models.Model):
    """Financial accounting for customers"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounting"
    )

    # Accounts assigned to this customer
    receivable_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="customer_receivables"
    )
    revenue_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="customer_revenues",
        blank=True,
        null=True,
    )

    # Accounting metrics
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ytd_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"Accounting for {self.user.email}"


class Bill(models.Model):
    """Supplier invoice (bill to be paid)"""

    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("verified", "Verified"),
        ("approved", "Approved"),
        ("paid", "Paid"),
        ("partial", "Partially Paid"),
        ("cancelled", "Cancelled"),
        ("disputed", "Disputed"),
    )

    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="bills")
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="bills",
    )

    bill_number = models.CharField(max_length=50)
    reference = models.CharField(max_length=100, blank=True, null=True)
    bill_date = models.DateField()
    due_date = models.DateField()

    amount = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0)]
    )
    tax_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    paid_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="bills",
    )
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="created_bills"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-bill_date", "-id"]
        unique_together = ("vendor", "bill_number")

    def __str__(self):
        return f"{self.vendor.procurement_vendor.supplier.name} - {self.bill_number}"

    @property
    def total_amount(self):
        return self.amount + self.tax_amount

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount

    @property
    def is_paid(self):
        return self.paid_amount >= self.total_amount

    @property
    def is_overdue(self):
        if self.status in ["paid", "cancelled"]:
            return False
        return self.due_date < timezone.now().date()


class BillLine(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=255)
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="bill_lines"
    )
    amount = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0)]
    )
    tax_rate = models.DecimalField(
        max_digits=6, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.description} (${self.amount})"

    @property
    def tax_amount(self):
        return self.amount * self.tax_rate / 100


class BillPayment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ("bank_transfer", "Bank Transfer"),
        ("check", "Check"),
        ("cash", "Cash"),
        ("credit_card", "Credit Card"),
        ("other", "Other"),
    )

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="payments")
    payment_date = models.DateField()
    amount = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0)]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="bill_payments",
    )

    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="bill_payments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-id"]

    def __str__(self):
        return f"Payment of ${self.amount} for {self.bill.bill_number}"


class Invoice(models.Model):
    """Customer invoice"""

    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("partially_paid", "Partially Paid"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    )

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="invoices"
    )
    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL, blank=True, null=True, related_name="invoices"
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    invoice_date = models.DateField()
    due_date = models.DateField()

    amount = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0)]
    )
    tax_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    paid_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="invoices",
    )
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_invoices",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-invoice_date", "-id"]

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer.user.email}"

    @property
    def total_amount(self):
        return self.amount + self.tax_amount

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount

    @property
    def is_paid(self):
        return self.paid_amount >= self.total_amount


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=255)
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="invoice_lines"
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0)]
    )
    tax_rate = models.DecimalField(
        max_digits=6, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.description} ({self.quantity} x ${self.unit_price})"

    @property
    def amount(self):
        return self.quantity * self.unit_price

    @property
    def tax_amount(self):
        return self.amount * self.tax_rate / 100

    @property
    def total_amount(self):
        return self.amount + self.tax_amount


class InvoicePayment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ("bank_transfer", "Bank Transfer"),
        ("check", "Check"),
        ("cash", "Cash"),
        ("credit_card", "Credit Card"),
        ("paypal", "PayPal"),
        ("stripe", "Stripe"),
        ("other", "Other"),
    )

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="payments"
    )
    payment_date = models.DateField()
    amount = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0)]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="invoice_payments",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-id"]

    def __str__(self):
        return f"Payment of ${self.amount} for {self.invoice.invoice_number}"


class TaxRate(models.Model):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(
        max_digits=6, decimal_places=2, validators=[MinValueValidator(0)]
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # Associated accounts
    sales_tax_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="sales_tax_rates"
    )
    purchase_tax_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="purchase_tax_rates"
    )

    def __str__(self):
        return f"{self.name} ({self.rate}%)"


class FinancialPeriod(models.Model):
    STATUS_CHOICES = (
        ("open", "Open"),
        ("closed", "Closed"),
    )

    fiscal_year = models.ForeignKey(
        FiscalYear, on_delete=models.CASCADE, related_name="periods"
    )
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    # Closing information
    closed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="closed_periods",
    )
    closed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["start_date"]
        unique_together = ("fiscal_year", "name")

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"


class FinancialStatement(models.Model):
    STATEMENT_TYPES = (
        ("balance_sheet", "Balance Sheet"),
        ("income_statement", "Income Statement"),
        ("cash_flow", "Cash Flow Statement"),
        ("retained_earnings", "Statement of Retained Earnings"),
        ("trial_balance", "Trial Balance"),
    )

    statement_type = models.CharField(max_length=50, choices=STATEMENT_TYPES)
    fiscal_year = models.ForeignKey(
        FiscalYear, on_delete=models.CASCADE, related_name="financial_statements"
    )
    period = models.ForeignKey(
        FinancialPeriod,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="financial_statements",
    )

    title = models.CharField(max_length=255)
    as_of_date = models.DateField()
    notes = models.TextField(blank=True, null=True)

    # The statement data could be stored as a JSON blob or in related data tables
    data = models.JSONField(blank=True, null=True)

    # Who generated this statement
    generated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="generated_statements",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-as_of_date", "statement_type"]

    def __str__(self):
        return f"{self.get_statement_type_display()} - {self.as_of_date}"
