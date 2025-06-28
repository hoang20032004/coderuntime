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
                
                # In ra thông tin trade để theo dõi
                print(f"[{datetime.datetime.now()}] {symbol}: {trade}")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Lỗi xử lý message: {e}")

def on_error(ws, error):
    print(f"[{datetime.datetime.now()}] WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[{datetime.datetime.now()}] WebSocket đã đóng. Code: {close_status_code}, Message: {close_msg}")


def run_ws_enhanced():
    """Chạy WebSocket với auto-reconnect cho background worker"""
    while True:
        try:
            print(f"[{datetime.datetime.now()}] Đang kết nối WebSocket...")
            ws = websocket.WebSocketApp(WEBSOCKET_URL,
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_close=on_close)
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"[{datetime.datetime.now()}] Lỗi WebSocket: {e}")
            print("Đang thử kết nối lại sau 10 giây...")
            time.sleep(10)

def save_data_periodically():
    """Lưu dữ liệu định kỳ để tránh mất dữ liệu"""
    global raw_data_df
    while True:
        try:
            if not raw_data_df.empty:
                filename = f"trading_data_{datetime.datetime.now().strftime('%Y%m%d_%H')}.csv"
                raw_data_df.to_csv(filename, index=False)
                print(f"[{datetime.datetime.now()}] Đã lưu {len(raw_data_df)} bản ghi vào {filename}")
                # Reset DataFrame sau khi lưu để tiết kiệm memory
                raw_data_df = pd.DataFrame()
            time.sleep(300)  # Lưu mỗi 5 phút
        except Exception as e:
            print(f"[{datetime.datetime.now()}] Lỗi khi lưu dữ liệu: {e}")
            time.sleep(60)

if __name__ == "__main__":
    print(f"[{datetime.datetime.now()}] Bắt đầu Trading Data Collector...")
    print("Đây là background worker - sẽ chạy liên tục...")
    
    # Khởi động thread lưu dữ liệu
    save_thread = threading.Thread(target=save_data_periodically, daemon=True)
    save_thread.start()
    
    # Khởi động thread WebSocket
    ws_thread = threading.Thread(target=run_ws_enhanced, daemon=True)
    ws_thread.start()
    
    # Giữ main thread chạy
    try:
        while True:
            time.sleep(60)
            print(f"[{datetime.datetime.now()}] Worker đang hoạt động. Dữ liệu hiện tại: {len(raw_data_df)} bản ghi")
    except KeyboardInterrupt:
        print("\n[Render] Worker đã dừng")  