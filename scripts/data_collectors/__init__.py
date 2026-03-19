"""
Data Collectors Package

Provides data collection from all integrated systems:
- Odoo (financial data)
- Social Media (Facebook, Instagram, Twitter)
- Email (Gmail activity)
- Audit Logs (system activity and health)

Usage:
    from scripts.data_collectors import aggregate_data

    data = aggregate_data(days=7)
"""

from scripts.data_collectors.odoo_collector import collect_odoo_data
from scripts.data_collectors.social_media_collector import collect_social_media_data
from scripts.data_collectors.email_collector import collect_email_data
from scripts.data_collectors.audit_log_collector import collect_audit_data
from scripts.data_collectors.aggregate_data import aggregate_data

__all__ = [
    'collect_odoo_data',
    'collect_social_media_data',
    'collect_email_data',
    'collect_audit_data',
    'aggregate_data'
]
