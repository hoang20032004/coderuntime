import websocket
import json
import datetime
import threading
import time
import requests
from flask import Flask, jsonify, request
import os

app = Flask(__name__)

# Define the WebSocket URL and instrument IDs
WEBSOCKET_URL = "wss://ws.bitget.com/v2/ws/public"
INSTRUMENT_IDS = ["SOLUSDT", "BTCUSDT", "ETHUSDT"]
collected_data = []
session_history = []

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
                
                if len(collected_data) % 50 == 0:
                    print(f"[{datetime.datetime.now()}] Collected {len(collected_data)} trades")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Message error: {e}")

def on_error(ws, error):
    print(f"[{datetime.datetime.now()}] WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[{datetime.datetime.now()}] WebSocket closed. Code: {close_status_code}")

# API Endpoints
@app.route('/')
def home():
    return jsonify({
        "service": "Trading Data Collector API",
        "status": "running",
        "endpoints": {
            "/api/latest": "Get latest collected data",
            "/api/summary": "Get data summary",
            "/api/history": "Get session history",
            "/api/symbols/<symbol>": "Get data for specific symbol"
        }
    })

@app.route('/api/latest')
def get_latest_data():
    """Lấy dữ liệu mới nhất"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify({
        "total_records": len(collected_data),
        "latest_trades": collected_data[-limit:] if collected_data else [],
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/summary')
def get_summary():
    """Tóm tắt dữ liệu"""
    if not collected_data:
        return jsonify({"message": "No data available"})
    
    # Tính toán thống kê
    symbols = {}
    for trade in collected_data:
        symbol = trade['symbol']
        if symbol not in symbols:
            symbols[symbol] = {"count": 0, "prices": []}
        symbols[symbol]["count"] += 1
        try:
            symbols[symbol]["prices"].append(float(trade['price']))
        except:
            pass
    
    # Tính giá trung bình
    for symbol in symbols:
        prices = symbols[symbol]["prices"]
        if prices:
            symbols[symbol]["avg_price"] = sum(prices) / len(prices)
            symbols[symbol]["min_price"] = min(prices)
            symbols[symbol]["max_price"] = max(prices)
    
    return jsonify({
        "total_trades": len(collected_data),
        "symbols": symbols,
        "data_range": {
            "first_trade": collected_data[0]['timestamp'] if collected_data else None,
            "last_trade": collected_data[-1]['timestamp'] if collected_data else None
        }
    })

@app.route('/api/symbols/<symbol>')
def get_symbol_data(symbol):
    """Lấy dữ liệu theo symbol cụ thể"""
    symbol_data = [trade for trade in collected_data if trade['symbol'] == symbol.upper()]
    return jsonify({
        "symbol": symbol.upper(),
        "count": len(symbol_data),
        "data": symbol_data[-50:]  # 50 trades gần nhất
    })

@app.route('/api/history')
def get_history():
    """Lịch sử các session"""
    return jsonify({
        "session_history": session_history,
        "current_session_count": len(collected_data)
    })

@app.route('/api/export')
def export_data():
    """Export toàn bộ dữ liệu"""
    return jsonify({
        "export_time": datetime.datetime.now().isoformat(),
        "total_records": len(collected_data),
        "data": collected_data
    })

def run_single_session():
    """Run single 5-minute data collection session"""
    global collected_data, session_history
    
    session_start = datetime.datetime.now()
    print(f"[{session_start}] Starting 5-minute session...")
    
    ws = websocket.WebSocketApp(WEBSOCKET_URL,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    ws_thread = threading.Thread(target=lambda: ws.run_forever(ping_interval=30, ping_timeout=10))
    ws_thread.daemon = True
    ws_thread.start()
    
    # Wait 5 minutes
    time.sleep(300)
    
    ws.close()
    session_end = datetime.datetime.now()
    
    # Lưu lịch sử session
    session_info = {
        "start_time": session_start.isoformat(),
        "end_time": session_end.isoformat(),
        "trades_collected": len(collected_data),
        "symbols": list(set([trade['symbol'] for trade in collected_data]))
    }
    session_history.append(session_info)
    
    # Giữ chỉ 10 session gần nhất
    if len(session_history) > 10:
        session_history = session_history[-10:]
    
    print(f"[{session_end}] Session ended. Collected {len(collected_data)} records")

def calculate_next_run_times():
    """Calculate next run times"""
    now = datetime.datetime.now()
    
    run_times = [
        now.replace(hour=9, minute=0, second=0, microsecond=0),
        now.replace(hour=15, minute=0, second=0, microsecond=0)
    ]
    
    next_run_times = []
    for run_time in run_times:
        if run_time > now:
            next_run_times.append(run_time)
        else:
            next_run_times.append(run_time + datetime.timedelta(days=1))
    
    return sorted(next_run_times)

def wait_for_next_run():
    """Wait for next scheduled run"""
    next_runs = calculate_next_run_times()
    next_run = next_runs[0]
    
    wait_seconds = (next_run - datetime.datetime.now()).total_seconds()
    
    print(f"[{datetime.datetime.now()}] Next run: {next_run}")
    print(f"[{datetime.datetime.now()}] Waiting {wait_seconds/3600:.1f} hours...")
    
    time.sleep(wait_seconds)

def background_scheduler():
    """Background scheduler cho data collection"""
    print(f"[{datetime.datetime.now()}] Trading Data Collector - 2x daily")
    print("Schedule: 9:00 AM & 3:00 PM, 5 minutes each")
    
    try:
        while True:
            wait_for_next_run()
            
            try:
                run_single_session()
            except Exception as e:
                print(f"[{datetime.datetime.now()}] Session error: {e}")
                
    except KeyboardInterrupt:
        print("\n[Render] Worker stopped")

if __name__ == "__main__":
    # Khởi động background scheduler
    scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Chạy Flask API
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
