# portfolio_tracker/models.py
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True, help_text="股票代號, e.g., AAPL")
    name = models.CharField(max_length=100, blank=True, null=True, help_text="公司名稱")
    last_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, help_text="最新成交價")
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
    updated_at = models.DateTimeField(auto_now=True, help_text="最後更新時間")

    class Meta:
        # 確保同一個標的、到期日、履約價和類型的組合是唯一的
        unique_together = ('underlying_stock', 'strike_price', 'expiration_date', 'option_type')
        ordering = ['expiration_date', 'strike_price']

    def __str__(self):
        return f"{self.underlying_stock.symbol} {self.expiration_date} ${self.strike_price} {self.get_option_type_display()}"

# --- 2. 使用者持倉與警報 ---

class Holding(models.Model):
    # GenericForeignKey 所需的三個欄位
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, help_text="關聯的內容類型 (Stock或Option)")
    object_id = models.PositiveIntegerField(help_text="關聯物件的 ID")
    instrument = GenericForeignKey('content_type', 'object_id')

    quantity = models.DecimalField(max_digits=12, decimal_places=4, help_text="持有數量/合約數")
    cost_basis = models.DecimalField(max_digits=12, decimal_places=4, help_text="平均持有成本（每股/每合約）")

    def __str__(self):
        return f"{self.quantity} of {self.instrument}"

class PriceAlert(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    instrument = GenericForeignKey('content_type', 'object_id')

    target_price = models.DecimalField(max_digits=12, decimal_places=4, help_text="目標價格")
    CONDITION_CHOICES = [('GTE', '>='), ('LTE', '<=')]
    condition = models.CharField(max_length=3, choices=CONDITION_CHOICES, help_text="觸發條件 (GTE: 大於等於, LTE: 小於等於)")
    
    STATUS_CHOICES = [('A', 'Active'), ('T', 'Triggered'), ('C', 'Cancelled')]
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A', help_text="警報狀態")

    def __str__(self):
        return f"Alert for {self.instrument} {self.condition} {self.target_price}"