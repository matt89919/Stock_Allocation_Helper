# portfolio_tracker/admin.py

from django.contrib import admin
from .models import (
    Stock, Option, Holding, Deposit, Transaction, RealizedGain, PortfolioSnapshot
)

# This makes your models visible on the admin site.
admin.site.register(Stock)
admin.site.register(Option)
admin.site.register(Holding)
admin.site.register(Deposit)
admin.site.register(Transaction)
admin.site.register(RealizedGain)
admin.site.register(PortfolioSnapshot)