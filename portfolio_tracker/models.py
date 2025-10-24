from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True, help_text="股票代號, e.g., AAPL")
    name = models.CharField(max_length=100, blank=True, null=True, help_text="公司名稱")
    last_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, help_text="最新成交價")
    previous_close = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, help_text="昨日收盤價")
    updated_at = models.DateTimeField(auto_now=True, help_text="最後更新時間")

    def __str__(self):
        return self.symbol

class Option(models.Model):
    underlying_stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='options', help_text="標的股票")
    strike_price = models.DecimalField(max_digits=12, decimal_places=4, help_text="履約價")
    expiration_date = models.DateField(help_text="到期日")
    OPTION_TYPE_CHOICES = [('C', 'Call'), ('P', 'Put')]
    option_type = models.CharField(max_length=1, choices=OPTION_TYPE_CHOICES, help_text="期權類型")
    
    occ_symbol = models.CharField(max_length=30, unique=True, null=True, blank=True, help_text="期權合約代號")
    last_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, help_text="最新成交價")
    previous_close = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, help_text="昨日收盤價")
    updated_at = models.DateTimeField(auto_now=True, help_text="最後更新時間")

    class Meta:
        unique_together = ('underlying_stock', 'strike_price', 'expiration_date', 'option_type')
        ordering = ['expiration_date', 'strike_price']

    def __str__(self):
        return f"{self.underlying_stock.symbol} {self.expiration_date} ${self.strike_price:.2f} {self.get_option_type_display()}"

class Holding(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, help_text="關聯的內容類型 (Stock或Option)")
    object_id = models.PositiveIntegerField(help_text="關聯物件的 ID")
    instrument = GenericForeignKey('content_type', 'object_id')

    quantity = models.DecimalField(max_digits=12, decimal_places=4, help_text="持有數量/合約數")
    cost_basis = models.DecimalField(max_digits=12, decimal_places=4, help_text="平均持有成本（每股/每合約）")

    def __str__(self):
        return f"{self.quantity} of {self.instrument}"

class PortfolioSnapshot(models.Model):
    date = models.DateField(unique=True)
    total_value = models.DecimalField(max_digits=15, decimal_places=4)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.date}: ${self.total_value}"

# --- NEW MODELS FOR TRANSACTION SYSTEM ---

class Deposit(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount of cash deposited")
    date = models.DateTimeField(default=timezone.now, help_text="Date of the deposit")

    def __str__(self):
        return f"Deposit of ${self.amount} on {self.date.strftime('%Y-%m-%d')}"

class Transaction(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    instrument = GenericForeignKey('content_type', 'object_id')
    
    TRANSACTION_TYPE_CHOICES = [('buy', 'Buy'), ('sell', 'Sell')]
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPE_CHOICES)
    
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4, help_text="Price per share/contract for this transaction")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} {self.quantity} of {self.instrument} at ${self.price}"

class RealizedGain(models.Model):
    instrument_name = models.CharField(max_length=100)
    realized_pnl = models.DecimalField(max_digits=12, decimal_places=2, help_text="Profit or Loss from a sell transaction")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.instrument_name}: ${self.realized_pnl}"

