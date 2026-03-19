"""
Odoo Data Collector

Collects financial data from Odoo for business intelligence reporting.
Retrieves invoices, payments, revenue, and expense data.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_servers.odoo_client import OdooClient


class OdooDataCollector:
    """Collects financial data from Odoo."""

    def __init__(self):
        """Initialize Odoo data collector."""
        self.client = OdooClient()
        self.client.authenticate()

    def collect_financial_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Collect financial data for a date range.

        Args:
            start_date: Start date (ISO format, default: 7 days ago)
            end_date: End date (ISO format, default: today)

        Returns:
            Dict with revenue, expenses, invoices, payments
        """
        # Default to last 7 days
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        try:
            # Get invoices
            invoices = self.client.list_invoices(
                filters=[
                    ('invoice_date', '>=', start_date),
                    ('invoice_date', '<=', end_date)
                ]
            )

            # Calculate totals
            total_revenue = 0
            total_expenses = 0
            invoice_count = 0
            paid_count = 0

            for invoice in invoices:
                amount = invoice.get('amount_total', 0)
                state = invoice.get('state', 'draft')
                move_type = invoice.get('move_type', 'out_invoice')

                if move_type == 'out_invoice':  # Customer invoice
                    total_revenue += amount
                elif move_type == 'in_invoice':  # Vendor bill
                    total_expenses += amount

                invoice_count += 1
                if state == 'posted':
                    paid_count += 1

            return {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': {
                    'total_revenue': round(total_revenue, 2),
                    'total_expenses': round(total_expenses, 2),
                    'net_profit': round(total_revenue - total_expenses, 2),
                    'invoice_count': invoice_count,
                    'paid_count': paid_count,
                    'pending_count': invoice_count - paid_count
                },
                'invoices': invoices,
                'collected_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'collected_at': datetime.now().isoformat()
            }

    def collect_customer_data(self) -> Dict[str, Any]:
        """
        Collect customer/partner data from Odoo.

        Returns:
            Dict with customer count and top customers
        """
        try:
            # Get all customers
            customers = self.client.models.execute_kw(
                self.client.db,
                self.client.uid,
                self.client.password,
                'res.partner',
                'search_read',
                [[('customer_rank', '>', 0)]],
                {'fields': ['name', 'email', 'phone'], 'limit': 100}
            )

            return {
                'customer_count': len(customers),
                'customers': customers[:10],  # Top 10
                'collected_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'collected_at': datetime.now().isoformat()
            }


def collect_odoo_data(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to collect Odoo data.

    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)

    Returns:
        Dict with financial and customer data
    """
    collector = OdooDataCollector()

    return {
        'financial': collector.collect_financial_data(start_date, end_date),
        'customers': collector.collect_customer_data()
    }


if __name__ == "__main__":
    """Test the collector."""
    print("Collecting Odoo data...")
    data = collect_odoo_data()

    print("\n=== Financial Summary ===")
    financial = data.get('financial', {})
    summary = financial.get('summary', {})
    print(f"Revenue: ${summary.get('total_revenue', 0):.2f}")
    print(f"Expenses: ${summary.get('total_expenses', 0):.2f}")
    print(f"Net Profit: ${summary.get('net_profit', 0):.2f}")
    print(f"Invoices: {summary.get('invoice_count', 0)}")

    print("\n=== Customer Summary ===")
    customers = data.get('customers', {})
    print(f"Total Customers: {customers.get('customer_count', 0)}")
