# portfolio_tracker/data_fetcher.py
import finnhub
from django.conf import settings
from typing import Union

import requests

# ------------------- 初始化 Finnhub Client -------------------
# 我們只在程式啟動時初始化一次，而不是在每次函式呼叫時都初始化
# 這樣效率更高
finnhub_client = None
if hasattr(settings, 'FINNHUB_API_TOKEN'):
    finnhub_client = finnhub.Client(api_key=settings.FINNHUB_API_TOKEN)
else:
    # 拋出一個警告，這樣在啟動時就能發現問題
    print("警告：FINNHUB_API_TOKEN 未在 settings.py 中設定。API 請求將會失敗。")

# -----------------------------------------------------------

def fetch_stock_data_from_finnhub(symbol: str) -> Union[dict, None]:
    """
    使用 finnhub-python 官方函式庫獲取最新報價。
    """
    if not finnhub_client:
        return None

    try:
        # 函式庫的使用方式，非常直觀！
        quote = finnhub_client.quote(symbol)
        
        # 'c' = current price (當前價格)
        # 'pc' = previous close price (昨日收盤價)
        price = quote.get('c')
        if price is None or price == 0:
            price = quote.get('pc')

        if price is not None:
            return {"price": price}
        else:
            print(f"從 Finnhub 獲取 {symbol} 數據時，價格為空。 回應: {quote}")
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
