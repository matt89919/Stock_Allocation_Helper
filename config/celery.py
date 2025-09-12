# config/celery.py
import os
from celery import Celery

# 設定 Django settings 模組的環境變數
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# 使用字串，這樣 worker 就不需要序列化設定物件
# namespace='CELERY' 表示所有 Celery 相關的設定鍵都應該以 'CELERY_' 開頭
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自動從所有已註冊的 Django app 中載入 tasks.py
app.autodiscover_tasks()