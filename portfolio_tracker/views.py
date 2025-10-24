from datetime import date, timedelta
from decimal import Decimal
from django.forms import DecimalField
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import (
    PortfolioSnapshot, Stock, Option, Holding, Deposit, Transaction, RealizedGain
)
from .serializers import (
    PortfolioSnapshotSerializer, StockSerializer, OptionSerializer, HoldingSerializer,
    DepositSerializer, TransactionSerializer, RealizedGainSerializer
)
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, F, DecimalField, Case, When, Value

class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer

class OptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer

class HoldingViewSet(viewsets.ModelViewSet):
    queryset = Holding.objects.all()
    serializer_class = HoldingSerializer

class PortfolioHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PortfolioSnapshotSerializer
    def get_queryset(self):
        thirty_days_ago = date.today() - timedelta(days=30)
        return PortfolioSnapshot.objects.filter(date__gte=thirty_days_ago)

# --- NEW VIEWSETS AND VIEWS ---

class DepositViewSet(viewsets.ModelViewSet):
    queryset = Deposit.objects.all()
    serializer_class = DepositSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        underlying_stock, _ = Stock.objects.get_or_create(symbol=data['symbol'].upper())
        is_option = all(k in data and data[k] is not None for k in ['strike_price', 'expiration_date', 'option_type'])

        if is_option:
            instrument, _ = Option.objects.get_or_create(
                underlying_stock=underlying_stock,
                strike_price=data['strike_price'],
                expiration_date=data['expiration_date'],
                option_type=data['option_type'].upper()
            )
        else:
            instrument = underlying_stock
        
        ctype = ContentType.objects.get_for_model(instrument)
        quantity = data['quantity']
        price = data['price']

        if data['transaction_type'] == 'buy':
            holding, created = Holding.objects.get_or_create(
                content_type=ctype, object_id=instrument.id,
                defaults={'quantity': 0, 'cost_basis': 0}
            )
            new_quantity = holding.quantity + quantity
            new_total_cost = (holding.quantity * holding.cost_basis) + (quantity * price)
            holding.cost_basis = new_total_cost / new_quantity
            holding.quantity = new_quantity
            holding.save()

        elif data['transaction_type'] == 'sell':
            try:
                holding = Holding.objects.get(content_type=ctype, object_id=instrument.id)
            except Holding.DoesNotExist:
                return Response({"error": "No holding found to sell."}, status=status.HTTP_400_BAD_REQUEST)
            
            if quantity > holding.quantity:
                return Response({"error": f"Cannot sell more than you own. You have {holding.quantity}."}, status=status.HTTP_400_BAD_REQUEST)

            cost_of_sold_shares = holding.cost_basis * quantity
            sale_proceeds = price * quantity
            gain_or_loss = sale_proceeds - cost_of_sold_shares
            RealizedGain.objects.create(instrument_name=str(instrument), realized_pnl=gain_or_loss)

            holding.quantity -= quantity
            if holding.quantity <= 0:
                holding.delete()
            else:
                holding.save()

        Transaction.objects.create(instrument=instrument, transaction_type=data['transaction_type'], quantity=quantity, price=price)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def portfolio_summary_view(request):
    """
    Provides a summary of total deposits, total realized gains, and free cash.
    """
    total_deposits = Deposit.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_realized_gains = RealizedGain.objects.aggregate(total=Sum('realized_pnl'))['total'] or Decimal('0.00')

    # --- CORRECTED FREE CASH CALCULATION ---
    # Get the ContentType for the Option model
    option_content_type = ContentType.objects.get_for_model(Option)

    # Calculate total cost of buys with a conditional multiplier for options
    total_buy_cost = Transaction.objects.filter(transaction_type='buy').aggregate(
        total=Sum(
            Case(
                When(content_type=option_content_type, then=(F('price') * F('quantity') * Value(100))),
                default=(F('price') * F('quantity')),
                output_field=DecimalField()
            )
        )
    )['total'] or Decimal('0.00')

    # Calculate total proceeds from sells with a conditional multiplier for options
    total_sell_proceeds = Transaction.objects.filter(transaction_type='sell').aggregate(
        total=Sum(
            Case(
                When(content_type=option_content_type, then=(F('price') * F('quantity') * Value(100))),
                default=(F('price') * F('quantity')),
                output_field=DecimalField()
            )
        )
    )['total'] or Decimal('0.00')

    # Calculate free cash
    free_cash = total_deposits - total_buy_cost + total_sell_proceeds
    
    return Response({
        "total_deposits": total_deposits,
        "total_realized_gains": total_realized_gains,
        "free_cash": free_cash,
    })