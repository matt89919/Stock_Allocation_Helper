# portfolio_tracker/data_fetcher.py
import datetime
import time
import finnhub
from django.conf import settings
from typing import List, Union

import requests

finnhub_client = None
if hasattr(settings, 'FINNHUB_API_TOKEN'):
    finnhub_client = finnhub.Client(api_key=settings.FINNHUB_API_TOKEN)
else:
    # 拋出一個警告，這樣在啟動時就能發現問題
    print("警告：FINNHUB_API_TOKEN 未在 settings.py 中設定。API 請求將會失敗。")

# -----------------------------------------------------------

def fetch_stock_data_from_finnhub(symbol: str) -> Union[dict, None]:
    """
    使用 finnhub-python 官方函式庫獲取最新報價和昨日收盤價。
    """
    if not finnhub_client:
        return None

    try:
        # 函式庫的使用方式，非常直觀！
        quote = finnhub_client.quote(symbol)
        
        # 'c' = current price (當前價格)
        # 'pc' = previous close price (昨日收盤價)
        current_price = quote.get('c')
        prev_close = quote.get('pc')

        # 如果當前價格為空或0，使用昨日收盤價作為備用
        if not current_price and prev_close:
            current_price = prev_close

        if current_price is not None and prev_close is not None:
            return {"price": current_price, "previous_close": prev_close}
        else:
            print(f"從 Finnhub 獲取 {symbol} 數據時，數據不完整。 回應: {quote}")
            return None

    except finnhub.FinnhubAPIException as e:
        print(f"Finnhub API 錯誤 (查詢 {symbol}): {e}")
        return None
    except Exception as e:
        print(f"獲取 {symbol} 數據時發生未知錯誤: {e}")
        return None
    
    

def fetch_option_chain_from_finnhub_requests(underlying_symbol: str) -> Union[dict, None]:
    """
    使用 requests 手動獲取指定股票的完整期權鏈。
    """
    if not hasattr(settings, 'FINNHUB_API_TOKEN'):
        print("錯誤：請在 settings.py 中設定 FINNHUB_API_TOKEN")
        return None

    api_token = settings.FINNHUB_API_TOKEN
    url = "https://finnhub.io/api/v1/stock/option-chain"
    params = {
        "symbol": underlying_symbol,
        "token": api_token
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # 檢查請求是否成功 (狀態碼 2xx)
        chain = response.json()
        
        if chain and chain.get('data'):
            return chain
        else:
            print(f"從 Finnhub 獲取 {underlying_symbol} 期權鏈時，回傳數據為空。")
            return None
            
    except Exception as e:
        print(f"使用 requests 獲取 {underlying_symbol} 期權鏈時發生未知錯誤: {e}")
        return None

def fetch_benchmark_candles_from_alpha_vantage(symbol: str) -> List[dict]:
    """ Fetches historical daily stock prices from Alpha Vantage. """
    api_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
    if not api_key:
        print("WARNING: ALPHA_VANTAGE_API_KEY is not set.")
        return []

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "Error Message" in data or not data.get("Time Series (Daily)"):
            print(f"Alpha Vantage API Error or unexpected response: {data}")
            return []

        time_series = data["Time Series (Daily)"]
        candles = [{'date': date_str, 'price': float(values['4. close'])} for date_str, values in time_series.items()]
        return candles[::-1] # Reverse to be in chronological order
    except Exception as e:
        print(f"An error occurred fetching from Alpha Vantage: {e}")
        return []