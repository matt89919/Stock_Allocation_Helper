# portfolio_tracker/admin.py
from django.contrib import admin
from .models import Stock, Option, Holding, PriceAlert

# @admin.register() 是一個更優雅的註冊方式
# 我們可以為每個模型客製化它在後台的顯示方式

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'last_price', 'updated_at')
    search_fields = ('symbol', 'name')

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('underlying_stock', 'expiration_date', 'strike_price', 'option_type', 'last_price', 'updated_at')
    list_filter = ('underlying_stock', 'expiration_date', 'option_type')
    search_fields = ('occ_symbol',)

@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'quantity', 'cost_basis')
    # raw_id_fields 可以在有大量關聯物件時提升效能


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'target_price', 'condition', 'status')
    list_filter = ('status', 'condition')
