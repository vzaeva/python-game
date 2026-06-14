import os
import runpy
import threading
import time
import traceback
from pathlib import Path
from flask import Flask
app = Flask(__name__)
BOT_PATH = Path(__file__).with_name("bot.py")
def run_bot_forever():
    while True:
        try:
            runpy.run_path(str(BOT_PATH), run_name="__main__")
        except Exception:
            traceback.print_exc()
            time.sleep(5)
@app.get("/")
def index():
    return "VK bot is running", 200
@app.get("/health")
def health():
    return {"status": "ok"}, 200
if os.environ.get("RUN_BOT_THREAD", "1") == "1":
    thread = threading.Thread(target=run_bot_forever, daemon=True)
    thread.start()