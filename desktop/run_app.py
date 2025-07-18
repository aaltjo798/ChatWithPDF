import webview
import threading
import subprocess
import time
import sys
import os
import requests

OLLAMA_PORT = 11434
OLLAMA_URL = f'http://localhost:{OLLAMA_PORT}'


def is_ollama_running():
    try:
        r = requests.get(OLLAMA_URL + '/api/tags', timeout=2)
        return r.status_code == 200
    except Exception:
        return False

def start_ollama():
    # Start ollama serve in the background
    try:
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Failed to start Ollama: {e}")

def start_flask():
    python_executable = sys.executable
    app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app.py'))
    subprocess.Popen([python_executable, app_path])

if __name__ == '__main__':
    # Ensure Ollama is running
    if not is_ollama_running():
        print("Ollama is not running. Starting Ollama server...")
        start_ollama()
        # Wait a bit for Ollama to start
        for _ in range(10):
            if is_ollama_running():
                break
            time.sleep(1)
        else:
            print("Failed to start Ollama. Please ensure Ollama is installed and in your PATH.")
    else:
        print("Ollama is already running.")

    threading.Thread(target=start_flask, daemon=True).start()
    time.sleep(2)  # Wait for Flask to start
    webview.create_window('Chat with PDF', 'http://127.0.0.1:5000')
    webview.start() 