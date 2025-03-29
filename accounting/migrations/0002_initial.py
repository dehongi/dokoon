# Generated by Django 5.1.7 on 2025-03-28 23:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounting', '0001_initial'),
        ('accounts', '0001_initial'),
        ('inventory', '0001_initial'),
        ('procurement', '0001_initial'),
        ('shop', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_bills', to='accounts.customuser'),
        ),
        migrations.AddField(
            model_name='bill',
            name='purchase_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bills', to='inventory.purchaseorder'),
        ),
        migrations.AddField(
            model_name='billline',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bill_lines', to='accounting.account'),
        ),
        migrations.AddField(
            model_name='billline',
            name='bill',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='accounting.bill'),
        ),
        migrations.AddField(
            model_name='billpayment',
            name='bill',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='accounting.bill'),
        ),
        migrations.AddField(
            model_name='billpayment',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bill_payments', to='accounts.customuser'),
        ),
        migrations.AddField(
            model_name='customer',
            name='receivable_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='customer_receivables', to='accounting.account'),
        ),
        migrations.AddField(
            model_name='customer',
            name='revenue_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='customer_revenues', to='accounting.account'),
        ),
        migrations.AddField(
            model_name='customer',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='accounting', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='financialperiod',
            name='closed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='closed_periods', to='accounts.customuser'),
        ),
        migrations.AddField(
            model_name='financialstatement',
            name='generated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_statements', to='accounts.customuser'),
        ),
        migrations.AddField(
            model_name='financialstatement',
            name='period',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='financial_statements', to='accounting.financialperiod'),
        ),
        migrations.AddField(
            model_name='financialstatement',
            name='fiscal_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financial_statements', to='accounting.fiscalyear'),
        ),
        migrations.AddField(
            model_name='financialperiod',
            name='fiscal_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='periods', to='accounting.fiscalyear'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_invoices', to='accounts.customuser'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='invoices', to='accounting.customer'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='shop.order'),
        ),
        migrations.AddField(
            model_name='invoiceline',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='invoice_lines', to='accounting.account'),
        ),
        migrations.AddField(
            model_name='invoiceline',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='accounting.invoice'),
        ),
        migrations.AddField(
            model_name='invoicepayment',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='accounting.invoice'),
        ),
        migrations.AddField(
            model_name='journalentry',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_journal_entries', to='accounts.customuser'),
        ),
        migrations.AddField(
            model_name='journalentry',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_journal_entries', to='accounts.customuser'),
        ),
        migrations.AddField(
            model_name='journalentry',
            name='fiscal_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='journal_entries', to='accounting.fiscalyear'),
        ),
        migrations.AddField(
            model_name='journalentry',
            name='journal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entries', to='accounting.journal'),
        ),
        migrations.AddField(
            model_name='journalentry',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='journal_entries', to='shop.order'),
        ),
        migrations.AddField(
            model_name='journalentry',
            name='purchase_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='journal_entries', to='inventory.purchaseorder'),
        ),
        migrations.AddField(
            model_name='invoicepayment',
            name='journal_entry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoice_payments', to='accounting.journalentry'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='journal_entry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='accounting.journalentry'),
        ),
        migrations.AddField(
            model_name='billpayment',
            name='journal_entry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bill_payments', to='accounting.journalentry'),
        ),
        migrations.AddField(
            model_name='bill',
            name='journal_entry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bills', to='accounting.journalentry'),
        ),
        migrations.AddField(
            model_name='journalentryline',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='journal_lines', to='accounting.account'),
        ),
        migrations.AddField(
            model_name='journalentryline',
            name='journal_entry',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='accounting.journalentry'),
        ),
        migrations.AddField(
            model_name='taxrate',
            name='purchase_tax_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='purchase_tax_rates', to='accounting.account'),
        ),
        migrations.AddField(
            model_name='taxrate',
            name='sales_tax_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sales_tax_rates', to='accounting.account'),
        ),
        migrations.AddField(
            model_name='vendor',
            name='expense_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='vendor_expenses', to='accounting.account'),
        ),
        migrations.AddField(
            model_name='vendor',
            name='payable_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='vendor_payables', to='accounting.account'),
        ),
        migrations.AddField(
            model_name='vendor',
            name='procurement_vendor',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='accounting', to='procurement.vendor'),
        ),
        migrations.AddField(
            model_name='bill',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bills', to='accounting.vendor'),
        ),
        migrations.AlterUniqueTogether(
            name='financialperiod',
            unique_together={('fiscal_year', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='bill',
            unique_together={('vendor', 'bill_number')},
        ),
    ]
