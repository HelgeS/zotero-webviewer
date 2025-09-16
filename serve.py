#!/usr/bin/env python3
"""
Simple script to serve the Literature Webviewer locally.
This resolves CORS issues when viewing the website.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def main():
    # Change to output directory
    output_dir = Path(__file__).parent / "output"
    if not output_dir.exists():
        print("❌ Output directory not found. Please run 'uv run build' first.")
        sys.exit(1)
    
    os.chdir(output_dir)
    
    # Start server
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            url = f"http://localhost:{PORT}"
            print(f"✅ Literature Webviewer server started!")
            print(f"🌐 Open in browser: {url}")
            print(f"📁 Serving from: {output_dir}")
            print(f"⏹️  Press Ctrl+C to stop")
            print()
            
            # Try to open browser automatically
            try:
                webbrowser.open(url)
                print(f"🚀 Opened {url} in your default browser")
            except:
                print(f"💡 Please manually open {url} in your browser")
            
            print()
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use.")
            print(f"💡 Try opening http://localhost:{PORT} in your browser")
            print(f"💡 Or stop the existing server and run this script again")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()