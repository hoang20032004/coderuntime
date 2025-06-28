import websocket
import json
import datetime
import threading
import time

WEBSOCKET_URL = "wss://ws.bitget.com/v2/ws/public"
INSTRUMENT_IDS = ["BTCUSDT"]
collected_data = []

def on_open(ws):
    print(f"[{datetime.datetime.now()}] WebSocket connected!")
    for inst_id in INSTRUMENT_IDS:
        message = {
            "op": "subscribe",
            "args": [{"instType": "SPOT", "channel": "trade", "instId": inst_id}]
        }
        ws.send(json.dumps(message))

def on_message(ws, message_str):  
    global collected_data
    try:
        data = json.loads(message_str)
        if "data" in data and data["data"]:
            collected_data.append(data)
            print(f"Trade received: {len(collected_data)} total")
    except:
        pass

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

if __name__ == "__main__":
    print("Starting immediate test...")
    
    ws = websocket.WebSocketApp(WEBSOCKET_URL,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    # Run for 1 minute to test
    ws_thread = threading.Thread(target=lambda: ws.run_forever())
    ws_thread.daemon = True
    ws_thread.start()
    
    time.sleep(60)  # Test for 1 minute
    
    print(f"Test completed. Collected {len(collected_data)} trades")
    
    # Keep alive for Render
    while True:
        time.sleep(300)
        print(f"[{datetime.datetime.now()}] Still running...")
