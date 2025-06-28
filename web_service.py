# Web Service version - có HTTP endpoint
from flask import Flask, jsonify
import threading
import time
import datetime
import pandas as pd
import websocket
import json
import os

app = Flask(__name__)

# Import từ trading_data.py
from trading_data import run_single_session, calculate_next_run_times

# Global variables
last_run_data = {"status": "waiting", "next_run": None, "data_count": 0}

@app.route('/')
def home():
    return jsonify({
        "service": "Trading Data Collector",
        "status": "active",
        "schedule": "9:00 AM & 3:00 PM daily",
        "last_run": last_run_data
    })

@app.route('/status')
def status():
    next_runs = calculate_next_run_times()
    return jsonify({
        "current_time": datetime.datetime.now().isoformat(),
        "next_run": next_runs[0].isoformat(),
        "schedule": ["09:00", "15:00"],
        "last_data_count": last_run_data.get("data_count", 0)
    })

@app.route('/run-now')
def run_now():
    """Endpoint để chạy thu thập dữ liệu ngay lập tức"""
    try:
        run_single_session()
        return jsonify({"status": "success", "message": "Data collection completed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def background_scheduler():
    """Chạy scheduler trong background"""
    global last_run_data
    
    while True:
        try:
            # Tính toán thời gian chờ
            next_runs = calculate_next_run_times()
            next_run = next_runs[0]
            wait_seconds = (next_run - datetime.datetime.now()).total_seconds()
            
            last_run_data["next_run"] = next_run.isoformat()
            last_run_data["status"] = "waiting"
            
            print(f"Next run: {next_run}, waiting {wait_seconds/3600:.1f} hours")
            
            time.sleep(wait_seconds)
            
            # Chạy thu thập dữ liệu
            last_run_data["status"] = "running"
            run_single_session()
            last_run_data["status"] = "completed"
            
        except Exception as e:
            print(f"Scheduler error: {e}")
            last_run_data["status"] = "error"
            time.sleep(300)  # Chờ 5 phút nếu có lỗi

if __name__ == "__main__":
    # Khởi động background scheduler
    scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Chạy Flask web service
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
