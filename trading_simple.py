import websocket
import json
import datetime
import threading
import time
import requests

# Define the WebSocket URL and instrument IDs
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
                    'data': trade
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

def run_single_session():
    """Run single 5-minute data collection session"""
    global collected_data
    
    print(f"[{datetime.datetime.now()}] Starting 5-minute session...")
    
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
    print(f"[{datetime.datetime.now()}] Session ended. Collected {len(collected_data)} records")
    
    # Save data as JSON
    if collected_data:
        filename = f"trading_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, 'w') as f:
            json.dump(collected_data, f, indent=2)
        print(f"[{datetime.datetime.now()}] Data saved to {filename}")
        collected_data = []

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

if __name__ == "__main__":
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
