import webview
import threading
import uvicorn
import sys
import os
import time
import urllib.request

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app 

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def wait_for_server():
    """Health check to ensure backend is ready before launching GUI."""
    url = "http://127.0.0.1:8000"
    retries = 20
    print(f"Waiting for server at {url}...")
    for i in range(retries):
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    print("Server is ready!")
                    return
        except Exception:
            time.sleep(0.5)
    print("Warning: Server execution timed out, launching GUI anyway...")

if __name__ == '__main__':
    # Start Backend in Thread
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    
    # Wait for Health Check
    wait_for_server()

    # Launch GUI
    # debug=True allows Right-Click -> Inspect Element for debuggingJS
    window = webview.create_window(
        title='Omni-IDE (Production Build)', 
        url='http://localhost:8000',
        width=1200,
        height=800,
        resizable=True,
        confirm_close=True
    )
    webview.start(debug=True)
