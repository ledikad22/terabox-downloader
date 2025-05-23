from flask import Flask, request, redirect, jsonify, send_file
from time import time
import requests

app = Flask(__name__)

# Rate limiting setup
rate_limit_store = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 5      # max requests per window

@app.before_request
def rate_limiter():
    ip = request.remote_addr
    now = time()

    if ip not in rate_limit_store:
        rate_limit_store[ip] = []

    rate_limit_store[ip] = [
        ts for ts in rate_limit_store[ip] if now - ts < RATE_LIMIT_WINDOW
    ]

    if len(rate_limit_store[ip]) >= RATE_LIMIT_MAX:
        return jsonify({"error": "Too many requests. Please wait a minute."}), 429

    rate_limit_store[ip].append(now)

@app.route('/')
def serve_frontend():
    return send_file("index.html")

@app.route('/download', methods=['GET'])
def auto_redirect():
    url = request.args.get("url")
    if not url:
        return "❌ Missing ?url= parameter", 400

    # Extract surl code
    if "surl=" in url:
        surl = url.split("surl=")[-1]
    else:
        surl = url.rstrip('/').split('/')[-1]

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.terabox.com/",
        "Content-Type": "application/json"
    }

    payload = {
        "app_id": "250528",
        "shorturl": surl
    }

    try:
        res = requests.post("https://www.terabox.com/share/list", headers=headers, json=payload)
        result = res.json()

        file_list = result.get("list", [])
        if not file_list:
            return "❌ No files found for this link", 404

        dlink = file_list[0].get("dlink")
        if not dlink:
            return "❌ Download link not available", 404

        return redirect(dlink)

    except Exception as e:
        return f"❌ Error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
