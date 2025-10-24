# portfolio_tracker/tasks.py
from datetime import date
import time
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Stock, Option, Holding, PortfolioSnapshot
from .data_fetcher import fetch_stock_data_from_finnhub, fetch_option_chain_from_finnhub_requests


@shared_task
def update_stock_price(stock_id: int):
    """
    [Worker Task]
    Updates a single stock's price and previous close, then broadcasts the change.
    """
    try:
        stock = Stock.objects.get(id=stock_id)
        data = fetch_stock_data_from_finnhub(stock.symbol)

        if data:
            new_price = data['price']
            new_previous_close = data['previous_close']
            
            if stock.last_price != new_price or stock.previous_close != new_previous_close:
                stock.last_price = new_price
                stock.previous_close = new_previous_close
                stock.save()
                print(f"✅ STOCK UPDATE: {stock.symbol} to {new_price}.")

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "price_updates",
                    {
                        "type": "price.update",
                        "data": { "symbol": stock.symbol, "price": float(new_price) },
                    },
                )
    except Stock.DoesNotExist:
        print(f"❌ ERROR: Stock with id {stock_id} not found.")
    except Exception as e:
        print(f"❌ ERROR updating stock id {stock_id}: {e}")

@shared_task
def sync_all_stock_prices():
    """
    [Manager Task]
    Dispatches update tasks for all stocks in the database.
    """
    print("🚀 Dispatching tasks to sync all stock prices...")
    for stock in Stock.objects.all():
        update_stock_price.delay(stock.id)
        time.sleep(1) 
    print("✅ All stock update tasks dispatched.")

# (Other tasks remain the same)

@shared_task
def update_option_prices_for_stock(stock_id: int):
    """
    [Worker Task]
    Fetches the entire option chain and updates only the last_price for contracts.
    """
    try:
        stock = Stock.objects.get(id=stock_id)
        print(f"Updating options for underlying stock: {stock.symbol}...")
        chain = fetch_option_chain_from_finnhub_requests(stock.symbol)
        if not chain:
            return

        updated_count = 0
        for expiration_data in chain.get('data', []):
            for option_type in ['CALL', 'PUT']:
                for contract_data in expiration_data.get('options', {}).get(option_type, []):
                    try:
                        option_obj = Option.objects.get(
                            underlying_stock=stock,
                            expiration_date=expiration_data['expirationDate'],
                            strike_price=contract_data['strike'],
                            option_type=option_type[0]
                        )
                        
                        new_price = contract_data.get('lastPrice')
                        
                        # CLEANUP: Removed the non-working previous_close logic
                        if new_price is not None and option_obj.last_price != new_price:
                            option_obj.last_price = new_price
                            option_obj.save()
                            updated_count += 1
                            
                    except Option.DoesNotExist:
                        continue 
        
        if updated_count > 0:
            print(f"✅ OPTION UPDATE: Updated {updated_count} contracts for {stock.symbol}.")

    except Stock.DoesNotExist:
        print(f"❌ ERROR: Stock with id {stock_id} not found for option update.")

@shared_task
def sync_all_option_prices():
    # (This task remains the same)
    print("🚀 Dispatching tasks to sync all option prices...")
    stocks_with_options_ids = Option.objects.values_list('underlying_stock_id', flat=True).distinct()
    for stock_id in stocks_with_options_ids:
        update_option_prices_for_stock.delay(stock_id)
        time.sleep(1)
    print(f"✅ Dispatched option chain updates for {len(stocks_with_options_ids)} underlying stocks.")

# --- NEW TASK TO FIX "DAY'S P&L" FOR OPTIONS ---
@shared_task
def snapshot_option_prices_as_previous_close():
    """
    [Daily Task]
    This task should be run once per day after market close.
    It takes the current 'last_price' of all options and saves it
    to the 'previous_close' field to be used on the next trading day.
    """
    print("📸 Starting daily snapshot of option prices...")
    updated_count = 0
    for option in Option.objects.all():
        if option.last_price is not None:
            option.previous_close = option.last_price
            option.save()
            updated_count += 1
    print(f"✅ Snapshotted {updated_count} option prices as previous_close.")


@shared_task
def create_daily_portfolio_snapshot():
    # (This task remains the same)
    total_value = 0
    holdings = Holding.objects.all()

    for holding in holdings:
        instrument = holding.instrument
        if hasattr(instrument, 'last_price') and instrument.last_price is not None:
            multiplier = 100 if isinstance(instrument, Option) else 1
            total_value += holding.quantity * instrument.last_price * multiplier

    PortfolioSnapshot.objects.update_or_create(
        date=date.today(),
        defaults={'total_value': total_value}
    )
    return f"Created snapshot for {date.today()} with value {total_value}"

