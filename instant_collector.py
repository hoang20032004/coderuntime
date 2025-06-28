import websocket
import json
import datetime
import threading
import time
from flask import Flask, jsonify
import os

app = Flask(__name__)

WEBSOCKET_URL = "wss://ws.bitget.com/v2/ws/public"
INSTRUMENT_IDS = ["SOLUSDT", "BTCUSDT", "ETHUSDT"]
collected_data = []

def on_open(ws):
    print(f"[{datetime.datetime.now()}] WebSocket connected!")
    for inst_id in INSTRUMENT_IDS:
        message = {
            "op": "subscribe",
            "args": [{"instType": "SPOT", "channel": "trade", "instId": inst_id}]
        }
        ws.send(json.dumps(message))
        print(f"[{datetime.datetime.now()}] Subscribed to {inst_id}")

def on_message(ws, message_str):  
    global collected_data
    try:
        data = json.loads(message_str)
        if "data" in data and data["data"]:
            symbol = data.get("arg", {}).get("instId", "")
            for trade in data["data"]:
                trade_data = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'symbol': symbol,
                    'price': trade.get('px', '0'),
                    'size': trade.get('sz', '0'),
                    'side': trade.get('side', ''),
                    'trade_id': trade.get('tradeId', '')
                }
                collected_data.append(trade_data)
                
                if len(collected_data) % 10 == 0:
                    print(f"[{datetime.datetime.now()}] Collected {len(collected_data)} trades")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Message error: {e}")

def on_error(ws, error):
    print(f"[{datetime.datetime.now()}] WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[{datetime.datetime.now()}] WebSocket closed")

@app.route('/')
def home():
    return jsonify({
        "service": "Instant Trading Data Collector",
        "status": "running",
        "collected_trades": len(collected_data),
        "data": collected_data[-20:] if collected_data else []
    })

@app.route('/api/data')
def get_data():
    return jsonify({
        "total": len(collected_data),
        "latest": collected_data[-50:] if collected_data else []
    })

def start_websocket():
    """Bắt đầu thu thập dữ liệu ngay lập tức"""
    print(f"[{datetime.datetime.now()}] Starting INSTANT data collection...")
    
    ws = websocket.WebSocketApp(WEBSOCKET_URL,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    # Chạy liên tục
    ws.run_forever(ping_interval=30, ping_timeout=10)

if __name__ == "__main__":
    print("🚀 INSTANT Trading Data Collector")
    print("Starting WebSocket connection immediately...")
    
    # Khởi động WebSocket trong background
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()
    
    # Chạy Flask API
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
