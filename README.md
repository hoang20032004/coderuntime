# Trading Data Collector

Ứng dụng thu thập dữ liệu trading real-time từ Bitget WebSocket API.

## Tính năng
- Thu thập dữ liệu trading real-time cho SOLUSDT, BTCUSDT, ETHUSDT
- **Lịch chạy**: 2 lần/ngày (9:00 AM và 3:00 PM), mỗi lần 5 phút
- Auto-reconnect khi mất kết nối
- Lưu dữ liệu tự động sau mỗi session
- Tối ưu cho background worker (tiết kiệm tài nguyên)

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
Dữ liệu sẽ được lưu vào file CSV theo format: `trading_data_YYYYMMDD_HHMM.csv`
- Mỗi session (5 phút) tạo 1 file riêng
- File chứa timestamp, symbol và data giao dịch chi tiết

## Lịch chạy
- **Thời gian**: 9:00 AM và 3:00 PM (UTC) mỗi ngày
- **Thời lượng**: 5 phút mỗi lần
- **Tổng**: 10 phút/ngày (tiết kiệm tài nguyên)

## Monitoring
- Logs hiển thị thời gian chạy tiếp theo
- Worker tự động chờ giữa các session
- Render free tier có thể chạy tốt với lịch này