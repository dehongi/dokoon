from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Sum, Q, F, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse

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


@login_required
@permission_required("accounting.view_account")
def accounting_dashboard(request):
    """Main dashboard view for accounting app."""
    # Get current fiscal year and period
    current_fiscal_year = FiscalYear.objects.filter(is_active=True).first()

    # Get summary data
    accounts_count = Account.objects.filter(is_active=True).count()

    # Get accounts receivable balance
    receivable_accounts = Account.objects.filter(
        account_type__type="asset", name__icontains="receivable", is_active=True
    )
    receivable_balance = sum(account.current_balance for account in receivable_accounts)

    # Get accounts payable balance
    payable_accounts = Account.objects.filter(
        account_type__type="liability", name__icontains="payable", is_active=True
    )
    payable_balance = sum(account.current_balance for account in payable_accounts)

    # Get revenue and expense totals for current fiscal year
    if current_fiscal_year:
        revenue_accounts = Account.objects.filter(
            account_type__type="revenue", is_active=True
        )
        expense_accounts = Account.objects.filter(
            account_type__type="expense", is_active=True
        )

        revenue_total = sum(account.current_balance for account in revenue_accounts)
        expense_total = sum(account.current_balance for account in expense_accounts)

        profit_loss = revenue_total - expense_total
    else:
        revenue_total = expense_total = profit_loss = 0

    # Recent transactions
    recent_journal_entries = JournalEntry.objects.all().order_by(
        "-date", "-created_at"
    )[:10]

    # Unpaid bills
    unpaid_bills = Bill.objects.filter(
        status__in=["verified", "approved", "partial"]
    ).order_by("due_date")[:5]

    # Unpaid invoices
    unpaid_invoices = Invoice.objects.filter(
        status__in=["sent", "partially_paid", "overdue"]
    ).order_by("due_date")[:5]

    context = {
        "current_fiscal_year": current_fiscal_year,
        "accounts_count": accounts_count,
        "receivable_balance": receivable_balance,
        "payable_balance": payable_balance,
        "revenue_total": revenue_total,
        "expense_total": expense_total,
        "profit_loss": profit_loss,
        "recent_journal_entries": recent_journal_entries,
        "unpaid_bills": unpaid_bills,
        "unpaid_invoices": unpaid_invoices,
    }

    return render(request, "accounting/dashboard.html", context)


# Chart of Accounts Views
@login_required
@permission_required("accounting.view_account")
def account_list(request):
    """Display the chart of accounts."""
    account_types = AccountType.objects.all()

    # Get parent accounts (top level)
    parent_accounts = {}
    for account_type in account_types:
        parent_accounts[account_type.id] = Account.objects.filter(
            account_type=account_type, parent__isnull=True, is_active=True
        ).order_by("code")

    context = {
        "account_types": account_types,
        "parent_accounts": parent_accounts,
    }

    return render(request, "accounting/account_list.html", context)


@login_required
@permission_required("accounting.view_account")
def account_detail(request, account_id):
    """Display account details and transactions."""
    account = get_object_or_404(Account, id=account_id)

    # Get child accounts if any
    child_accounts = account.children.filter(is_active=True).order_by("code")

    # Get journal entry lines for this account
    journal_lines = (
        JournalEntryLine.objects.filter(account=account, journal_entry__status="posted")
        .select_related("journal_entry")
        .order_by("-journal_entry__date", "-journal_entry__id")
    )

    context = {
        "account": account,
        "child_accounts": child_accounts,
        "journal_lines": journal_lines,
    }

    return render(request, "accounting/account_detail.html", context)


# Journal Entry Views
@login_required
@permission_required("accounting.view_journalentry")
def journal_entry_list(request):
    """List journal entries with filters."""
    journal_entries = JournalEntry.objects.all()

    # Apply filters
    if "journal" in request.GET:
        journal_id = request.GET.get("journal")
        if journal_id:
            journal_entries = journal_entries.filter(journal_id=journal_id)

    if "status" in request.GET:
        status = request.GET.get("status")
        if status:
            journal_entries = journal_entries.filter(status=status)

    if "start_date" in request.GET and "end_date" in request.GET:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        if start_date and end_date:
            journal_entries = journal_entries.filter(date__range=[start_date, end_date])

    # Search
    if "q" in request.GET:
        query = request.GET.get("q")
        if query:
            journal_entries = journal_entries.filter(
                Q(entry_number__icontains=query)
                | Q(description__icontains=query)
                | Q(reference__icontains=query)
            )

    # Get all journals for filter dropdown
    journals = Journal.objects.filter(is_active=True)

    context = {
        "journal_entries": journal_entries.order_by("-date", "-id"),
        "journals": journals,
    }

    return render(request, "accounting/journal_entry_list.html", context)


@login_required
@permission_required("accounting.view_journalentry")
def journal_entry_detail(request, entry_id):
    """Display journal entry details."""
    journal_entry = get_object_or_404(JournalEntry, id=entry_id)
    lines = journal_entry.lines.all().order_by("-debit_amount", "credit_amount")

    context = {
        "journal_entry": journal_entry,
        "lines": lines,
    }

    return render(request, "accounting/journal_entry_detail.html", context)


@login_required
@permission_required("accounting.add_journalentry")
def journal_entry_create(request):
    """Create a new journal entry."""
    # Implementation would include form handling
    # This is a placeholder for the view logic

    if request.method == "POST":
        # Process form data and create journal entry
        # Redirect to the journal entry detail page
        pass

    # Get active fiscal year
    fiscal_year = FiscalYear.objects.filter(is_active=True).first()
    journals = Journal.objects.filter(is_active=True)
    accounts = Account.objects.filter(is_active=True).order_by("code")

    context = {
        "fiscal_year": fiscal_year,
        "journals": journals,
        "accounts": accounts,
    }

    return render(request, "accounting/journal_entry_form.html", context)


@login_required
@permission_required("accounting.change_journalentry")
def journal_entry_post(request, entry_id):
    """Post a journal entry."""
    journal_entry = get_object_or_404(JournalEntry, id=entry_id)

    if journal_entry.status != "draft":
        messages.error(request, "Only draft journal entries can be posted.")
        return redirect("accounting:journal_entry_detail", entry_id=entry_id)

    try:
        journal_entry.post(request.user)
        messages.success(
            request,
            f"Journal entry {journal_entry.entry_number} has been posted successfully.",
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("accounting:journal_entry_detail", entry_id=entry_id)


# Bill Views
@login_required
@permission_required("accounting.view_bill")
def bill_list(request):
    """List bills with filters."""
    bills = Bill.objects.all()

    # Apply filters
    if "status" in request.GET:
        status = request.GET.get("status")
        if status:
            bills = bills.filter(status=status)

    if "vendor" in request.GET:
        vendor_id = request.GET.get("vendor")
        if vendor_id:
            bills = bills.filter(vendor_id=vendor_id)

    if "start_date" in request.GET and "end_date" in request.GET:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        if start_date and end_date:
            bills = bills.filter(bill_date__range=[start_date, end_date])

    # Search
    if "q" in request.GET:
        query = request.GET.get("q")
        if query:
            bills = bills.filter(
                Q(bill_number__icontains=query)
                | Q(reference__icontains=query)
                | Q(vendor__procurement_vendor__supplier__name__icontains=query)
                | Q(notes__icontains=query)
            )

    # Get vendors for filter dropdown
    vendors = Vendor.objects.all()

    context = {
        "bills": bills.order_by("-bill_date", "-id"),
        "vendors": vendors,
    }

    return render(request, "accounting/bill_list.html", context)


@login_required
@permission_required("accounting.view_bill")
def bill_detail(request, bill_id):
    """Display bill details."""
    bill = get_object_or_404(Bill, id=bill_id)
    lines = bill.lines.all()
    payments = bill.payments.all().order_by("-payment_date", "-id")

    context = {
        "bill": bill,
        "lines": lines,
        "payments": payments,
    }

    return render(request, "accounting/bill_detail.html", context)


# Invoice Views
@login_required
@permission_required("accounting.view_invoice")
def invoice_list(request):
    """List invoices with filters."""
    invoices = Invoice.objects.all()

    # Apply filters
    if "status" in request.GET:
        status = request.GET.get("status")
        if status:
            invoices = invoices.filter(status=status)

    if "customer" in request.GET:
        customer_id = request.GET.get("customer")
        if customer_id:
            invoices = invoices.filter(customer_id=customer_id)

    if "start_date" in request.GET and "end_date" in request.GET:
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        if start_date and end_date:
            invoices = invoices.filter(invoice_date__range=[start_date, end_date])

    # Search
    if "q" in request.GET:
        query = request.GET.get("q")
        if query:
            invoices = invoices.filter(
                Q(invoice_number__icontains=query)
                | Q(reference__icontains=query)
                | Q(customer__user__email__icontains=query)
                | Q(customer__user__first_name__icontains=query)
                | Q(customer__user__last_name__icontains=query)
                | Q(notes__icontains=query)
            )

    # Get customers for filter dropdown
    customers = Customer.objects.all()

    context = {
        "invoices": invoices.order_by("-invoice_date", "-id"),
        "customers": customers,
    }

    return render(request, "accounting/invoice_list.html", context)


@login_required
@permission_required("accounting.view_invoice")
def invoice_detail(request, invoice_id):
    """Display invoice details."""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    lines = invoice.lines.all()
    payments = invoice.payments.all().order_by("-payment_date", "-id")

    context = {
        "invoice": invoice,
        "lines": lines,
        "payments": payments,
    }

    return render(request, "accounting/invoice_detail.html", context)


# Financial Reports
@login_required
@permission_required("accounting.view_financialstatement")
def balance_sheet(request):
    """Generate and display a balance sheet."""
    # Get fiscal year and period
    fiscal_year_id = request.GET.get("fiscal_year")
    period_id = request.GET.get("period")

    fiscal_year = None
    period = None
    as_of_date = timezone.now().date()

    if fiscal_year_id:
        fiscal_year = get_object_or_404(FiscalYear, id=fiscal_year_id)
        if period_id:
            period = get_object_or_404(
                FinancialPeriod, id=period_id, fiscal_year=fiscal_year
            )
            as_of_date = period.end_date
        else:
            as_of_date = fiscal_year.end_date

    # Get all asset accounts
    asset_accounts = Account.objects.filter(
        account_type__type="asset", is_active=True
    ).order_by("code")

    # Get all liability accounts
    liability_accounts = Account.objects.filter(
        account_type__type="liability", is_active=True
    ).order_by("code")

    # Get all equity accounts
    equity_accounts = Account.objects.filter(
        account_type__type="equity", is_active=True
    ).order_by("code")

    # Calculate totals
    total_assets = sum(account.current_balance for account in asset_accounts)
    total_liabilities = sum(account.current_balance for account in liability_accounts)
    total_equity = sum(account.current_balance for account in equity_accounts)

    # Get fiscal years for dropdown
    fiscal_years = FiscalYear.objects.all().order_by("-start_date")
    periods = []
    if fiscal_year:
        periods = fiscal_year.periods.all().order_by("start_date")

    context = {
        "asset_accounts": asset_accounts,
        "liability_accounts": liability_accounts,
        "equity_accounts": equity_accounts,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "fiscal_years": fiscal_years,
        "selected_fiscal_year": fiscal_year,
        "periods": periods,
        "selected_period": period,
        "as_of_date": as_of_date,
    }

    return render(request, "accounting/balance_sheet.html", context)


@login_required
@permission_required("accounting.view_financialstatement")
def income_statement(request):
    """Generate and display an income statement."""
    # Get fiscal year and period
    fiscal_year_id = request.GET.get("fiscal_year")
    period_id = request.GET.get("period")

    fiscal_year = None
    period = None
    start_date = end_date = None

    if fiscal_year_id:
        fiscal_year = get_object_or_404(FiscalYear, id=fiscal_year_id)
        start_date = fiscal_year.start_date
        end_date = fiscal_year.end_date

        if period_id:
            period = get_object_or_404(
                FinancialPeriod, id=period_id, fiscal_year=fiscal_year
            )
            start_date = period.start_date
            end_date = period.end_date
    else:
        # Default to current fiscal year
        fiscal_year = FiscalYear.objects.filter(is_active=True).first()
        if fiscal_year:
            start_date = fiscal_year.start_date
            end_date = fiscal_year.end_date

    # Get all revenue accounts
    revenue_accounts = Account.objects.filter(
        account_type__type="revenue", is_active=True
    ).order_by("code")

    # Get all expense accounts
    expense_accounts = Account.objects.filter(
        account_type__type="expense", is_active=True
    ).order_by("code")

    # Calculate totals
    total_revenue = sum(account.current_balance for account in revenue_accounts)
    total_expenses = sum(account.current_balance for account in expense_accounts)
    net_income = total_revenue - total_expenses

    # Get fiscal years for dropdown
    fiscal_years = FiscalYear.objects.all().order_by("-start_date")
    periods = []
    if fiscal_year:
        periods = fiscal_year.periods.all().order_by("start_date")

    context = {
        "revenue_accounts": revenue_accounts,
        "expense_accounts": expense_accounts,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_income": net_income,
        "fiscal_years": fiscal_years,
        "selected_fiscal_year": fiscal_year,
        "periods": periods,
        "selected_period": period,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "accounting/income_statement.html", context)


@login_required
@permission_required("accounting.view_financialstatement")
def trial_balance(request):
    """Generate and display a trial balance."""
    # Get fiscal year and period
    fiscal_year_id = request.GET.get("fiscal_year")
    period_id = request.GET.get("period")

    fiscal_year = None
    period = None
    as_of_date = timezone.now().date()

    if fiscal_year_id:
        fiscal_year = get_object_or_404(FiscalYear, id=fiscal_year_id)
        if period_id:
            period = get_object_or_404(
                FinancialPeriod, id=period_id, fiscal_year=fiscal_year
            )
            as_of_date = period.end_date
        else:
            as_of_date = fiscal_year.end_date

    # Get all accounts
    accounts = Account.objects.filter(is_active=True).order_by("code")

    # Prepare data for the trial balance
    trial_balance_data = []
    total_debits = 0
    total_credits = 0

    for account in accounts:
        if account.current_balance != 0:
            debit_amount = credit_amount = 0

            if account.is_debit_balance:
                # Asset and Expense accounts typically have debit balances
                if account.current_balance > 0:
                    debit_amount = account.current_balance
                else:
                    credit_amount = -account.current_balance
            else:
                # Liability, Equity, and Revenue accounts typically have credit balances
                if account.current_balance > 0:
                    credit_amount = account.current_balance
                else:
                    debit_amount = -account.current_balance

            total_debits += debit_amount
            total_credits += credit_amount

            trial_balance_data.append(
                {
                    "account": account,
                    "debit_amount": debit_amount,
                    "credit_amount": credit_amount,
                }
            )

    # Get fiscal years for dropdown
    fiscal_years = FiscalYear.objects.all().order_by("-start_date")
    periods = []
    if fiscal_year:
        periods = fiscal_year.periods.all().order_by("start_date")

    context = {
        "trial_balance_data": trial_balance_data,
        "total_debits": total_debits,
        "total_credits": total_credits,
        "is_balanced": total_debits == total_credits,
        "fiscal_years": fiscal_years,
        "selected_fiscal_year": fiscal_year,
        "periods": periods,
        "selected_period": period,
        "as_of_date": as_of_date,
    }

    return render(request, "accounting/trial_balance.html", context)
