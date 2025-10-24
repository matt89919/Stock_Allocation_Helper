from rest_framework import serializers
from .models import (
    PortfolioSnapshot, Stock, Option, Holding, Deposit, Transaction, RealizedGain
)

class StockSerializer(serializers.ModelSerializer):
    instrument_name = serializers.CharField(source='symbol', read_only=True)
    class Meta:
        model = Stock
        fields = ['symbol', 'name', 'last_price', 'previous_close', 'instrument_name']

class OptionSerializer(serializers.ModelSerializer):
    instrument_name = serializers.StringRelatedField(source='__str__')
    class Meta:
        model = Option
        fields = [
            'id', 'instrument_name', 'last_price', 'previous_close',
            'underlying_stock', 'strike_price', 'expiration_date', 'option_type'
        ]

class HoldingSerializer(serializers.ModelSerializer):
    instrument_name = serializers.StringRelatedField(source='instrument', read_only=True)
    class Meta:
        model = Holding
        fields = ['id', 'instrument_name', 'quantity', 'cost_basis']

class PortfolioSnapshotSerializer(serializers.ModelSerializer):
    value = serializers.DecimalField(max_digits=15, decimal_places=4, source='total_value')
    class Meta:
        model = PortfolioSnapshot
        fields = ['date', 'value']

# --- NEW SERIALIZERS for the transaction-based system ---

class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    # These extra fields are needed for the frontend to create a transaction,
    # but are not part of the Transaction model itself.
    symbol = serializers.CharField(write_only=True)
    strike_price = serializers.DecimalField(max_digits=12, decimal_places=4, write_only=True, required=False)
    expiration_date = serializers.DateField(write_only=True, required=False)
    option_type = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'quantity', 'price', 'date', 
            'symbol', 'strike_price', 'expiration_date', 'option_type'
        ]

class RealizedGainSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealizedGain
        fields = '__all__'

