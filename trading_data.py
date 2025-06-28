# import necessary libraries
import pandas
import websocket
import json
import datetime
import threading
import time
import pandas as pd
import requests

# # Define the WebSocket URL and instrument IDs

# url = "https://api.bitget.com/api/v2/spot/public/symbols"

# try:
#     response = requests.get(url, timeout=10)
#     data = response.json()

#     if response.status_code == 200 and data.get('code') == '00000':
#         usdt_pairs = [item['symbol'] for item in data['data']
#                       if item['status'] == 'online' and item['symbol'].endswith('USDT')]
#         print(usdt_pairs)
#     else:
#         print(" API trả về lỗi:", data.get('msg', 'Không rõ lỗi'))

# except Exception as e:
#     print(" Lỗi khi gọi API:", e)


# Define the WebSocket URL and instrument IDs
WEBSOCKET_URL = "wss://ws.bitget.com/v2/ws/public"
INSTRUMENT_IDS = ["SOLUSDT", "BTCUSDT", "ETHUSDT"]
raw_data_df = pd.DataFrame()


# Create a WebSocket app
def on_open(ws):
    print(f"[{datetime.datetime.now()}] WebSocket đã kết nối thành công!")
    for inst_id in INSTRUMENT_IDS:
        message = {
            "op": "subscribe",
            "args": [{"instType": "SPOT", "channel": "trade", "instId": inst_id}]
        }
        ws.send(json.dumps(message))
        print(f"[{datetime.datetime.now()}] Đã subscribe {inst_id}")

def on_message(ws, message_str):  
    global raw_data_df
    try:
        data = json.loads(message_str)
        if "data" in data and data["data"]:
            symbol = data.get("arg", {}).get("instId", "")
            for trade in data["data"]:
                new_row = pd.DataFrame([{
                    'timestamp': datetime.datetime.now(),
                    'symbol': symbol,
                    'data': trade
                }])
                raw_data_df = pd.concat([raw_data_df, new_row], ignore_index=True)
                
                # In ít thông tin hơn để không spam log
                if len(raw_data_df) % 50 == 0:  # In mỗi 50 trades
                    print(f"[{datetime.datetime.now()}] Đã thu thập {len(raw_data_df)} trades")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Lỗi xử lý message: {e}")

def on_error(ws, error):
    print(f"[{datetime.datetime.now()}] WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[{datetime.datetime.now()}] WebSocket đã đóng. Code: {close_status_code}, Message: {close_msg}")


def run_single_session():
    """Chạy 1 session thu thập dữ liệu trong 5 phút"""
    global raw_data_df
    
    print(f"[{datetime.datetime.now()}] Bắt đầu session thu thập dữ liệu (5 phút)...")
    
    # Tạo WebSocket connection
    ws = websocket.WebSocketApp(WEBSOCKET_URL,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    # Chạy WebSocket trong thread riêng
    ws_thread = threading.Thread(target=lambda: ws.run_forever(ping_interval=30, ping_timeout=10))
    ws_thread.daemon = True
    ws_thread.start()
    
    # Chờ 5 phút (300 giây)
    time.sleep(300)
    
    # Đóng WebSocket
    ws.close()
    print(f"[{datetime.datetime.now()}] Kết thúc session. Đã thu thập {len(raw_data_df)} bản ghi")
    
    # Lưu dữ liệu
    if not raw_data_df.empty:
        filename = f"trading_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        raw_data_df.to_csv(filename, index=False)
        print(f"[{datetime.datetime.now()}] Đã lưu dữ liệu vào {filename}")
        raw_data_df = pd.DataFrame()  # Reset DataFrame
    
def calculate_next_run_times():
    """Tính toán 2 thời điểm chạy trong ngày"""
    now = datetime.datetime.now()
    
    # Chạy lúc 9:00 và 15:00 hàng ngày
    run_times = [
        now.replace(hour=9, minute=0, second=0, microsecond=0),
        now.replace(hour=15, minute=0, second=0, microsecond=0)
    ]
    
    # Nếu đã qua cả 2 thời điểm trong ngày, chuyển sang ngày mai
    next_run_times = []
    for run_time in run_times:
        if run_time > now:
            next_run_times.append(run_time)
        else:
            # Chuyển sang ngày mai
            next_run_times.append(run_time + datetime.timedelta(days=1))
    
    return sorted(next_run_times)

def wait_for_next_run():
    """Chờ đến thời điểm chạy tiếp theo"""
    next_runs = calculate_next_run_times()
    next_run = next_runs[0]
    
    wait_seconds = (next_run - datetime.datetime.now()).total_seconds()
    
    print(f"[{datetime.datetime.now()}] Thời điểm chạy tiếp theo: {next_run}")
    print(f"[{datetime.datetime.now()}] Chờ {wait_seconds/3600:.1f} giờ...")
    
    time.sleep(wait_seconds)

if __name__ == "__main__":
    print(f"[{datetime.datetime.now()}] Trading Data Collector - Chế độ 2 lần/ngày")
    print("Lịch chạy: 9:00 AM và 3:00 PM, mỗi lần 5 phút")
    
    try:
        while True:
            # Chờ đến thời điểm chạy tiếp theo
            wait_for_next_run()
            
            # Chạy session thu thập dữ liệu
            try:
                run_single_session()
            except Exception as e:
                print(f"[{datetime.datetime.now()}] Lỗi trong session: {e}")
                
    except KeyboardInterrupt:
        print("\n[Render] Worker đã dừng")  