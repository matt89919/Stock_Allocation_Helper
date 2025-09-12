# Dockerfile

# 1. 選擇一個官方的 Python 基礎映像檔
# python:3.11-slim 是一個輕量化的版本，適合部署
FROM python:3.11-slim

# 2. 設定環境變數
# 確保 Python 的輸出日誌能即時顯示，而不是被緩存
ENV PYTHONUNBUFFERED=1

# 3. 在容器內建立一個工作目錄
WORKDIR /app

# 4. 複製並安裝專案依賴
# 先只複製 requirements.txt 是為了利用 Docker 的層快取機制
# 只有當這個檔案變更時，才會重新執行 pip install，加速建構
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 複製整個專案的程式碼到工作目錄
COPY . .