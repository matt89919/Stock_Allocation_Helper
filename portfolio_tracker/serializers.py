# portfolio_tracker/serializers.py
from rest_framework import serializers
from .models import Stock, Option, Holding, PriceAlert

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = '__all__'

class HoldingSerializer(serializers.ModelSerializer):
    # 為了在 API 中更清晰地顯示 instrument 名稱
    instrument_name = serializers.StringRelatedField(source='instrument', read_only=True)

    class Meta:
        model = Holding
        # 顯示 'instrument_name' 而不是 'content_type' 和 'object_id'
        fields = ['id', 'instrument_name', 'quantity', 'cost_basis', 'content_type', 'object_id']
        extra_kwargs = {
            'content_type': {'write_only': True}, # 這些欄位只在寫入時需要
            'object_id': {'write_only': True},
        }

class PriceAlertSerializer(serializers.ModelSerializer):
    instrument_name = serializers.StringRelatedField(source='instrument', read_only=True)

    class Meta:
        model = PriceAlert
        fields = ['id', 'instrument_name', 'target_price', 'condition', 'status', 'content_type', 'object_id']
        extra_kwargs = {
            'content_type': {'write_only': True},
            'object_id': {'write_only': True},
        }