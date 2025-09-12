# portfolio_tracker/tasks.py
from celery import shared_task
from .data_fetcher import fetch_stock_data_from_finnhub
from .data_fetcher import fetch_option_chain_from_finnhub_requests
from typing import Union
import time
from .models import PriceAlert, Stock, Option
from django.contrib.contenttypes.models import ContentType


@shared_task
def update_stock_price(stock_id: int):
    """
    [工人 Task]
    更新單一股票價格，並在成功後觸發相關警報檢查。
    """
    try:
        stock = Stock.objects.get(id=stock_id)
        symbol_for_api = stock.symbol

        print(f"背景任務：正在更新股票 {symbol_for_api}...")
        data = fetch_stock_data_from_finnhub(symbol_for_api)

        if data and data.get('price') is not None:
            stock.last_price = data['price']
            stock.save()
            print(f"✅ 成功更新 {stock.symbol}，最新價格: {stock.last_price}")

            # --- 新增的邏輯：觸發警報檢查 ---
            print(f"🔍 正在檢查與 {stock.symbol} 相關的警報...")
            # 找到這個 Stock 物件對應的 ContentType
            stock_content_type = ContentType.objects.get_for_model(stock)
            # 篩選出所有與這個 Stock 相關且狀態為 Active 的警報
            related_alerts = PriceAlert.objects.filter(
                content_type=stock_content_type, 
                object_id=stock.id, 
                status='A'
            )

            for alert in related_alerts:
                # 為每一個相關的警報派發一個檢查任務
                check_price_alert.delay(alert.id)
            # ---------------------------------
        else:
            print(f"⚠️ 未能獲取 {stock.symbol} 的數據。")

    except Stock.DoesNotExist:
        print(f"❌ 錯誤：在資料庫中找不到 ID 為 {stock_id} 的股票。")
    except Exception as e:
        print(f"❌ 更新股票 ID {stock_id} 時發生未知錯誤: {e}")


@shared_task
def sync_all_stock_prices():
    """
    [經理 Task]
    獲取資料庫中所有的股票，並為每一支股票派發一個更新任務。
    """
    print("🚀 開始同步所有股票價格的排程任務...")
    all_stocks = Stock.objects.all()
    if not all_stocks:
        print("資料庫中沒有股票，任務結束。")
        return

    for stock in all_stocks:
        # .delay() 是 Celery 的魔法
        # 它不會立即執行函式，而是將任務訊息發送到 Redis 隊列中
        # 等待空閒的 Worker 來領取並執行
        update_stock_price.delay(stock.id)
        time.sleep(1) # 每派發一個任務就稍微等待一下，避免瞬間請求過於頻繁

    print(f"✅ 所有 {len(all_stocks)} 支股票的更新任務已派發至隊列。")



@shared_task
def check_price_alert(alert_id: int):
    """
    [工人 Task]
    檢查單一價格警報的條件是否滿足。
    """
    try:
        alert = PriceAlert.objects.get(id=alert_id, status='A') # 只找活躍的警報
    except PriceAlert.DoesNotExist:
        # 如果警報不是 Active 或已被刪除，則直接返回
        return

    instrument = alert.instrument # 透過 GenericForeignKey 獲取關聯的 Stock 或 Option 物件
    if not instrument or instrument.last_price is None:
        # 如果關聯的物件不存在，或價格還沒更新，則跳過
        return

    current_price = instrument.last_price
    target_price = alert.target_price
    condition_met = False

    # 檢查條件
    if alert.condition == 'GTE' and current_price >= target_price:
        condition_met = True
    elif alert.condition == 'LTE' and current_price <= target_price:
        condition_met = True

    # 如果條件滿足
    if condition_met:
        print(f"🚨🚨🚨 到價通知觸發！ 🚨🚨🚨")
        print(f"警報 ID: {alert.id}, 工具: {instrument}, "
              f"條件: {current_price} {alert.get_condition_display()} {target_price}")

        # --- 未來可以在這裡加入發送 Email 或 WebSocket 通知的邏輯 ---

        # 將警報狀態更新為 "已觸發"
        alert.status = 'T' # 'T' for Triggered
        alert.save()


@shared_task
def check_all_active_alerts():
    """
    [備用經理 Task]
    定期全面檢查所有活躍的警報。
    """
    print("⚙️ 開始執行備用的全面警報檢查...")
    active_alerts = PriceAlert.objects.filter(status='A')
    for alert in active_alerts:
        check_price_alert.delay(alert.id)
    print(f"✅ 已為 {len(active_alerts)} 個活躍警報派發檢查任務。")


@shared_task
def update_option_prices_for_stock(stock_id: int):
    """
    [工人 Task]
    獲取一支標的股票的完整期權鏈，並更新資料庫中所有相關的期權價格。
    """
    try:
        stock = Stock.objects.get(id=stock_id)
        print(f"背景任務：正在更新 {stock.symbol} 的所有相關期權...")

        # 1. 進行一次 API 請求，獲取整個期權鏈
        chain = fetch_option_chain_from_finnhub_requests(stock.symbol)
        if not chain:
            return

        updated_count = 0
        # 2. 遍歷 API 回傳的數據，更新資料庫
        for expiration_data in chain.get('data', []):
            for option_type in ['CALL', 'PUT']:
                for contract_data in expiration_data.get('options', {}).get(option_type, []):
                    # 嘗試根據 API 回傳的數據，找到我們資料庫中對應的期權物件
                    try:
                        option_obj = Option.objects.get(
                            underlying_stock=stock,
                            expiration_date=expiration_data['expirationDate'],
                            strike_price=contract_data['strike'],
                            option_type=option_type[0] # 'CALL' -> 'C'
                        )

                        # 更新價格並儲存
                        option_obj.last_price = contract_data.get('lastPrice')
                        option_obj.save()
                        updated_count += 1

                        # 觸發相關的警報檢查
                        # (與 stock 任務中相同的邏輯)
                        option_content_type = ContentType.objects.get_for_model(option_obj)
                        related_alerts = PriceAlert.objects.filter(
                            content_type=option_content_type,
                            object_id=option_obj.id,
                            status='A'
                        )
                        for alert in related_alerts:
                            check_price_alert.delay(alert.id)

                    except Option.DoesNotExist:
                        # 如果資料庫中沒有追蹤這個合約，就略過
                        continue

        if updated_count > 0:
            print(f"✅ 成功更新了 {stock.symbol} 的 {updated_count} 個期權合約價格。")

    except Stock.DoesNotExist:
        print(f"❌ 錯誤：在資料庫中找不到 ID 為 {stock_id} 的股票。")

@shared_task
def sync_all_option_prices():
    """
    [經理 Task]
    找到所有被追蹤的期權（其標的股票），並為它們派發更新任務。
    """
    print("🚀 開始同步所有期權價格的排程任務...")

    # 找到所有在 Option 資料表中有紀錄的、不重複的 Stock ID
    stocks_with_options_ids = Option.objects.values_list('underlying_stock_id', flat=True).distinct()

    if not stocks_with_options_ids:
        print("資料庫中沒有期權，任務結束。")
        return

    for stock_id in stocks_with_options_ids:
        update_option_prices_for_stock.delay(stock_id)
        time.sleep(1) # 同樣稍微間隔

    print(f"✅ 所有 {len(stocks_with_options_ids)} 支相關股票的期權更新任務已派發至隊列。")