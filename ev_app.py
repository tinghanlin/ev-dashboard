from flask import Flask, jsonify, send_from_directory
import requests
import os
import time

app = Flask(__name__)

# Explicit charger order
CHARGER_IDS = [1389, 1391, 3232, 3233]

BASE_URL = "https://emsp.evpassport.com/web/api/v1/locations/chargers/"

# Cache setup
cache = {
    "data": None,
    "timestamp": 0
}
CACHE_DURATION = 30  # seconds

# Custom headers
HEADERS = {
    "User-Agent": (
        "EV-Dashboard/1.0 "
        "UChicago CS PhD student tired of clicking through multiple links just to see if a charger is available"
    )
}

@app.route("/chargers")
def get_chargers():
    now = time.time()

    if cache["data"] and now - cache["timestamp"] < CACHE_DURATION:
        return jsonify(cache["data"])

    results = []

    for cid in CHARGER_IDS:
        try:
            response = requests.get(
                BASE_URL + str(cid),
                headers=HEADERS,
                timeout=5
            )
            data = response.json()

            charger_status = data["content"]["charger"]["status"]

            results.append({
                "id": cid,
                "status": charger_status
            })

        except Exception:
            results.append({
                "id": cid,
                "status": "ERROR"
            })

    cache["data"] = results
    cache["timestamp"] = now

    return jsonify(results)

@app.route("/")
def serve_html():
    return send_from_directory(
        os.path.dirname(__file__),
        "check_charger.html"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)