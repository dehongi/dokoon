from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from shop.models import Order
from procurement.models import PurchaseOrder
from accounting.models import JournalEntry, Journal, Account, Bill, Invoice


@receiver(post_save, sender=Order)
def create_sales_journal_entry(sender, instance, created, **kwargs):
    """
    Create a journal entry when an order is marked as completed.
    """
    if (
        instance.status == "completed"
        and not JournalEntry.objects.filter(order=instance).exists()
    ):
        # Get or create the sales journal
        sales_journal, _ = Journal.objects.get_or_create(
            name="Sales Journal",
            defaults={"description": "Journal for sales transactions"},
        )

        # Create a new journal entry
        journal_entry = JournalEntry.objects.create(
            journal=sales_journal,
            reference=f"SO-{instance.order_number}",
            description=f"Sale to {instance.customer.name if hasattr(instance, 'customer') and instance.customer else 'Customer'}",
            order=instance,
            created_by=instance.updated_by if hasattr(instance, "updated_by") else None,
            status="draft",
        )

        # Get the accounts
        try:
            accounts_receivable = Account.objects.get(
                code="1200"
            )  # Accounts Receivable
            sales_revenue = Account.objects.get(code="4000")  # Sales Revenue
            inventory_asset = Account.objects.get(code="1300")  # Inventory Asset
            cogs = Account.objects.get(code="5000")  # Cost of Goods Sold

            # Create journal entry lines
            # Debit Accounts Receivable
            journal_entry.lines.create(
                account=accounts_receivable,
                description="Accounts Receivable",
                debit_amount=instance.total_amount,
                credit_amount=0,
            )

            # Credit Sales Revenue
            journal_entry.lines.create(
                account=sales_revenue,
                description="Sales Revenue",
                debit_amount=0,
                credit_amount=instance.total_amount,
            )

            # If we have COGS information
            if hasattr(instance, "total_cost"):
                # Debit COGS
                journal_entry.lines.create(
                    account=cogs,
                    description="Cost of Goods Sold",
                    debit_amount=instance.total_cost,
                    credit_amount=0,
                )

                # Credit Inventory Asset
                journal_entry.lines.create(
                    account=inventory_asset,
                    description="Inventory Asset",
                    debit_amount=0,
                    credit_amount=instance.total_cost,
                )

            # Auto-post the journal entry if it's balanced
            if journal_entry.is_balanced:
                journal_entry.status = "posted"
                journal_entry.posted_by = journal_entry.created_by
                journal_entry.save()

        except Account.DoesNotExist:
            # Handle case where required accounts don't exist
            pass


@receiver(post_save, sender=PurchaseOrder)
def create_purchase_journal_entry(sender, instance, created, **kwargs):
    """
    Create a journal entry when a purchase order is marked as received.
    """
    if (
        instance.status == "received"
        and not JournalEntry.objects.filter(purchase_order=instance).exists()
    ):
        # Get or create the purchases journal
        purchases_journal, _ = Journal.objects.get_or_create(
            name="Purchases Journal",
            defaults={"description": "Journal for purchase transactions"},
        )

        # Create a new journal entry
        journal_entry = JournalEntry.objects.create(
            journal=purchases_journal,
            reference=f"PO-{instance.po_number}",
            description=f"Purchase from {instance.vendor.name if hasattr(instance, 'vendor') and instance.vendor else 'Vendor'}",
            purchase_order=instance,
            created_by=instance.updated_by if hasattr(instance, "updated_by") else None,
            status="draft",
        )

        # Get the accounts
        try:
            accounts_payable = Account.objects.get(code="2100")  # Accounts Payable
            inventory_asset = Account.objects.get(code="1300")  # Inventory Asset

            # Create journal entry lines
            # Debit Inventory Asset
            journal_entry.lines.create(
                account=inventory_asset,
                description="Inventory Asset",
                debit_amount=instance.total_amount,
                credit_amount=0,
            )

            # Credit Accounts Payable
            journal_entry.lines.create(
                account=accounts_payable,
                description="Accounts Payable",
                debit_amount=0,
                credit_amount=instance.total_amount,
            )

            # Auto-post the journal entry if it's balanced
            if journal_entry.is_balanced:
                journal_entry.status = "posted"
                journal_entry.posted_by = journal_entry.created_by
                journal_entry.save()

        except Account.DoesNotExist:
            # Handle case where required accounts don't exist
            pass


@receiver(post_save, sender=Bill)
def create_bill_journal_entry(sender, instance, created, **kwargs):
    """
    Create a journal entry when a bill is created or updated.
    """
    # Only create a journal entry for new bills or when status changes to approved
    if created or instance.status_changed and instance.status == "approved":
        if not JournalEntry.objects.filter(
            reference=f"BILL-{instance.bill_number}"
        ).exists():
            # Get or create the purchases journal
            purchases_journal, _ = Journal.objects.get_or_create(
                name="Purchases Journal",
                defaults={"description": "Journal for purchase transactions"},
            )

            # Create a new journal entry
            journal_entry = JournalEntry.objects.create(
                journal=purchases_journal,
                reference=f"BILL-{instance.bill_number}",
                description=f"Bill from {instance.vendor.name}",
                created_by=(
                    instance.created_by if hasattr(instance, "created_by") else None
                ),
                status="draft",
            )

            # Get the accounts
            try:
                accounts_payable = Account.objects.get(code="2100")  # Accounts Payable

                # Create journal entry lines
                for line in instance.lines.all():
                    # Debit expense account or asset account
                    journal_entry.lines.create(
                        account=line.account,
                        description=line.description,
                        debit_amount=line.amount,
                        credit_amount=0,
                    )

                # Credit Accounts Payable
                journal_entry.lines.create(
                    account=accounts_payable,
                    description="Accounts Payable",
                    debit_amount=0,
                    credit_amount=instance.total_amount,
                )

                # Auto-post the journal entry if it's balanced and the bill is approved
                if journal_entry.is_balanced and instance.status == "approved":
                    journal_entry.status = "posted"
                    journal_entry.posted_by = journal_entry.created_by
                    journal_entry.save()

            except Account.DoesNotExist:
                # Handle case where required accounts don't exist
                pass


@receiver(post_save, sender=Invoice)
def create_invoice_journal_entry(sender, instance, created, **kwargs):
    """
    Create a journal entry when an invoice is created or updated.
    """
    # Only create a journal entry for new invoices or when status changes to approved
    if created or instance.status_changed and instance.status == "approved":
        if not JournalEntry.objects.filter(
            reference=f"INV-{instance.invoice_number}"
        ).exists():
            # Get or create the sales journal
            sales_journal, _ = Journal.objects.get_or_create(
                name="Sales Journal",
                defaults={"description": "Journal for sales transactions"},
            )

            # Create a new journal entry
            journal_entry = JournalEntry.objects.create(
                journal=sales_journal,
                reference=f"INV-{instance.invoice_number}",
                description=f"Invoice to {instance.customer.name}",
                created_by=(
                    instance.created_by if hasattr(instance, "created_by") else None
                ),
                status="draft",
            )

            # Get the accounts
            try:
                accounts_receivable = Account.objects.get(
                    code="1200"
                )  # Accounts Receivable

                # Credit revenue accounts
                for line in instance.lines.all():
                    journal_entry.lines.create(
                        account=line.account,
                        description=line.description,
                        debit_amount=0,
                        credit_amount=line.amount,
                    )

                # Debit Accounts Receivable
                journal_entry.lines.create(
                    account=accounts_receivable,
                    description="Accounts Receivable",
                    debit_amount=instance.total_amount,
                    credit_amount=0,
                )

                # Auto-post the journal entry if it's balanced and the invoice is approved
                if journal_entry.is_balanced and instance.status == "approved":
                    journal_entry.status = "posted"
                    journal_entry.posted_by = journal_entry.created_by
                    journal_entry.save()

            except Account.DoesNotExist:
                # Handle case where required accounts don't exist
                pass
