from django.urls import path
from . import views

app_name = "accounting"

urlpatterns = [
    # Dashboard
    path("", views.accounting_dashboard, name="dashboard"),
    # Chart of Accounts
    path("accounts/", views.account_list, name="account_list"),
    path("accounts/<int:account_id>/", views.account_detail, name="account_detail"),
    # Journal Entries
    path("journal-entries/", views.journal_entry_list, name="journal_entry_list"),
    path(
        "journal-entries/<int:entry_id>/",
        views.journal_entry_detail,
        name="journal_entry_detail",
    ),
    path(
        "journal-entries/create/",
        views.journal_entry_create,
        name="journal_entry_create",
    ),
    path(
        "journal-entries/<int:entry_id>/post/",
        views.journal_entry_post,
        name="journal_entry_post",
    ),
    # Bills (Accounts Payable)
    path("bills/", views.bill_list, name="bill_list"),
    path("bills/<int:bill_id>/", views.bill_detail, name="bill_detail"),
    # Invoices (Accounts Receivable)
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/<int:invoice_id>/", views.invoice_detail, name="invoice_detail"),
    # Financial Reports
    path("reports/balance-sheet/", views.balance_sheet, name="balance_sheet"),
    path("reports/income-statement/", views.income_statement, name="income_statement"),
    path("reports/trial-balance/", views.trial_balance, name="trial_balance"),
]
