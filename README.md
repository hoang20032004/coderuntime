# Trading Data Collector

Ứng dụng thu thập dữ liệu trading real-time từ Bitget WebSocket API.

## Tính năng
- Thu thập dữ liệu trading real-time cho SOLUSDT, BTCUSDT, ETHUSDT
- Auto-reconnect khi mất kết nối
- Lưu dữ liệu định kỳ vào file CSV
- Phù hợp để chạy trên background worker

## Deploy lên Render

### Bước 1: Tạo Background Worker
1. Đăng nhập vào [Render](https://render.com)
2. Tạo new service → Background Worker
3. Connect GitHub repository này

### Bước 2: Cấu hình
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python trading_data.py`
- **Environment**: Python 3

### Bước 3: Deploy
- Click "Create Background Worker"
- Render sẽ tự động build và deploy

## Chạy local
```bash
pip install -r requirements.txt
python trading_data.py
```

## File dữ liệu
Dữ liệu sẽ được lưu vào file CSV theo format: `trading_data_YYYYMMDD_HH.csv`

## Monitoring
- Logs sẽ hiển thị trong Render dashboard
- Worker sẽ tự động restart nếu crash
- Dữ liệu được lưu mỗi 5 phút để tránh mất dữ liệu