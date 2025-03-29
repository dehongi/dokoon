from django.contrib import admin
from .models import (
    FiscalYear,
    AccountType,
    Account,
    Journal,
    JournalEntry,
    JournalEntryLine,
    Vendor,
    Customer,
    Bill,
    BillLine,
    BillPayment,
    Invoice,
    InvoiceLine,
    InvoicePayment,
    TaxRate,
    FinancialPeriod,
    FinancialStatement,
)


class FinancialPeriodInline(admin.TabularInline):
    model = FinancialPeriod
    extra = 1


class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_active", "is_closed")
    list_filter = ("is_active", "is_closed")
    search_fields = ("name",)
    inlines = [FinancialPeriodInline]


class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "account_type",
        "parent",
        "current_balance",
        "is_active",
    )
    list_filter = ("account_type", "is_active")
    search_fields = ("code", "name", "description")
    readonly_fields = ("current_balance",)
    fieldsets = (
        (None, {"fields": ("code", "name", "account_type", "parent", "is_active")}),
        ("Description", {"fields": ("description",)}),
        ("Balance Information", {"fields": ("current_balance",)}),
    )


class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "description")
    list_filter = ("type",)
    search_fields = ("name", "description")


class JournalAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "description")


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 1
    fields = ("account", "description", "debit_amount", "credit_amount", "reference")


class JournalEntryAdmin(admin.ModelAdmin):
    list_display = (
        "entry_number",
        "date",
        "journal",
        "status",
        "total_amount",
        "is_balanced",
        "created_by",
    )
    list_filter = ("status", "journal", "date", "fiscal_year")
    search_fields = ("entry_number", "description", "reference")
    readonly_fields = (
        "is_balanced",
        "total_amount",
        "created_at",
        "updated_at",
        "posted_at",
    )
    inlines = [JournalEntryLineInline]
    fieldsets = (
        (
            None,
            {"fields": ("journal", "fiscal_year", "entry_number", "date", "status")},
        ),
        (
            "Description & References",
            {"fields": ("description", "reference", "order", "purchase_order")},
        ),
        ("Status Information", {"fields": ("is_balanced", "total_amount")}),
        (
            "Audit Information",
            {
                "fields": (
                    "created_by",
                    "approved_by",
                    "created_at",
                    "updated_at",
                    "posted_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def is_balanced(self, obj):
        return obj.is_balanced

    is_balanced.boolean = True
    is_balanced.short_description = "Balanced"


class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "procurement_vendor",
        "payable_account",
        "current_balance",
        "ytd_purchases",
    )
    search_fields = ("procurement_vendor__supplier__name",)
    readonly_fields = ("current_balance", "ytd_purchases")
    fieldsets = (
        (
            None,
            {"fields": ("procurement_vendor", "payable_account", "expense_account")},
        ),
        ("Financial Information", {"fields": ("current_balance", "ytd_purchases")}),
    )


class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "receivable_account",
        "current_balance",
        "credit_limit",
        "ytd_sales",
    )
    search_fields = ("user__email", "user__first_name", "user__last_name")
    readonly_fields = ("current_balance", "ytd_sales")
    fieldsets = (
        (None, {"fields": ("user", "receivable_account", "revenue_account")}),
        (
            "Financial Information",
            {"fields": ("current_balance", "credit_limit", "ytd_sales")},
        ),
    )


class BillLineInline(admin.TabularInline):
    model = BillLine
    extra = 1
    fields = ("description", "account", "amount", "tax_rate", "tax_amount")
    readonly_fields = ("tax_amount",)


class BillPaymentInline(admin.TabularInline):
    model = BillPayment
    extra = 0
    fields = ("payment_date", "amount", "payment_method", "reference", "journal_entry")
    readonly_fields = ("journal_entry",)


class BillAdmin(admin.ModelAdmin):
    list_display = (
        "bill_number",
        "vendor",
        "bill_date",
        "due_date",
        "total_amount",
        "paid_amount",
        "is_paid",
        "status",
    )
    list_filter = ("status", "bill_date", "due_date", "vendor")
    search_fields = (
        "bill_number",
        "reference",
        "vendor__procurement_vendor__supplier__name",
        "notes",
    )
    readonly_fields = (
        "total_amount",
        "is_paid",
        "remaining_amount",
        "is_overdue",
        "created_at",
        "updated_at",
    )
    inlines = [BillLineInline, BillPaymentInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "vendor",
                    "purchase_order",
                    "bill_number",
                    "reference",
                    "status",
                )
            },
        ),
        ("Date Information", {"fields": ("bill_date", "due_date")}),
        (
            "Amount Information",
            {
                "fields": (
                    "amount",
                    "tax_amount",
                    "total_amount",
                    "paid_amount",
                    "remaining_amount",
                )
            },
        ),
        ("Status Information", {"fields": ("is_paid", "is_overdue", "journal_entry")}),
        (
            "Additional Information",
            {"fields": ("notes", "created_by", "created_at", "updated_at")},
        ),
    )

    def is_paid(self, obj):
        return obj.is_paid

    is_paid.boolean = True
    is_paid.short_description = "Paid"

    def is_overdue(self, obj):
        return obj.is_overdue

    is_overdue.boolean = True
    is_overdue.short_description = "Overdue"


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1
    fields = (
        "description",
        "account",
        "quantity",
        "unit_price",
        "amount",
        "tax_rate",
        "tax_amount",
        "total_amount",
    )
    readonly_fields = ("amount", "tax_amount", "total_amount")


class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0
    fields = ("payment_date", "amount", "payment_method", "reference", "journal_entry")
    readonly_fields = ("journal_entry",)


class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "customer",
        "invoice_date",
        "due_date",
        "total_amount",
        "paid_amount",
        "remaining_amount",
        "status",
    )
    list_filter = ("status", "invoice_date", "due_date")
    search_fields = ("invoice_number", "reference", "customer__user__email", "notes")
    readonly_fields = (
        "total_amount",
        "remaining_amount",
        "is_paid",
        "created_at",
        "updated_at",
    )
    inlines = [InvoiceLineInline, InvoicePaymentInline]
    fieldsets = (
        (
            None,
            {"fields": ("customer", "order", "invoice_number", "reference", "status")},
        ),
        ("Date Information", {"fields": ("invoice_date", "due_date")}),
        (
            "Amount Information",
            {
                "fields": (
                    "amount",
                    "tax_amount",
                    "total_amount",
                    "paid_amount",
                    "remaining_amount",
                )
            },
        ),
        ("Status Information", {"fields": ("is_paid", "journal_entry")}),
        (
            "Additional Information",
            {"fields": ("notes", "created_by", "created_at", "updated_at")},
        ),
    )

    def is_paid(self, obj):
        return obj.is_paid

    is_paid.boolean = True
    is_paid.short_description = "Paid"


class TaxRateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "rate",
        "sales_tax_account",
        "purchase_tax_account",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "description")


class FinancialPeriodAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "fiscal_year",
        "start_date",
        "end_date",
        "status",
        "closed_at",
    )
    list_filter = ("status", "fiscal_year")
    search_fields = ("name",)
    readonly_fields = ("closed_at", "closed_by")
    fieldsets = (
        (None, {"fields": ("fiscal_year", "name", "status")}),
        ("Date Range", {"fields": ("start_date", "end_date")}),
        ("Closing Information", {"fields": ("closed_by", "closed_at")}),
    )


class FinancialStatementAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "statement_type",
        "fiscal_year",
        "period",
        "as_of_date",
        "generated_by",
        "generated_at",
    )
    list_filter = ("statement_type", "fiscal_year", "as_of_date")
    search_fields = ("title", "notes")
    readonly_fields = ("generated_at", "generated_by")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "statement_type",
                    "title",
                    "fiscal_year",
                    "period",
                    "as_of_date",
                )
            },
        ),
        ("Data", {"fields": ("data", "notes")}),
        ("Generation Information", {"fields": ("generated_by", "generated_at")}),
    )


# Register all models
admin.site.register(FiscalYear, FiscalYearAdmin)
admin.site.register(AccountType, AccountTypeAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Journal, JournalAdmin)
admin.site.register(JournalEntry, JournalEntryAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(TaxRate, TaxRateAdmin)
admin.site.register(FinancialPeriod, FinancialPeriodAdmin)
admin.site.register(FinancialStatement, FinancialStatementAdmin)
