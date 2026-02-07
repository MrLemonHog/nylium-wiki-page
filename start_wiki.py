import http.server
import socketserver
import subprocess
import webbrowser
import sys
import os
import time

PORT = 8000
NEXO_GENERATOR = "nexo-items.py"
RENDERER_SCRIPT = "renderer.py"
HTML_FILE = "wiki-copy.html"

class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run_script(script_name):
    print(f"Running {script_name}...")
    
    if not os.path.exists(script_name):
        print(f"Error: {script_name} not found")
        return False

    try:
        subprocess.run(
            [sys.executable, script_name], 
            check=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing {script_name}: code {e.returncode}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def start_wiki_server():
    if not os.path.exists(HTML_FILE):
        print(f"Warning: {HTML_FILE} missing")

    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with ReuseAddrTCPServer(("", PORT), handler) as httpd:
            url = f"http://localhost:{PORT}/{HTML_FILE}"
            print(f"Server started at {url}")
            
            time.sleep(1)
            webbrowser.open(url)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    if run_script(NEXO_GENERATOR):
        if run_script(RENDERER_SCRIPT):
            start_wiki_server()
        else:
            print("Renderer script failed")
    else:
        print("Generator script failed")