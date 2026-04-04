from flask import Flask, jsonify, send_from_directory
import requests
import os
import time

app = Flask(__name__)

# Explicit charger order
CHARGER_IDS = [1389, 1391, 3232, 3233]

BASE_URL = "https://emsp.evpassport.com/web/api/v2/locations/chargers/"

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


def fetch_charger_status(charger_id):
    response = requests.get(
        BASE_URL + str(charger_id),
        headers=HEADERS,
        timeout=5
    )
    response.raise_for_status()
    data = response.json()

    charger = data.get("charger", {})
    charger_status = charger.get("status")

    if not charger_status:
        evses = charger.get("evses", [])
        connector_statuses = [
            evse.get("status")
            or evse.get("connector", {}).get("statusLabel")
            or evse.get("connector", {}).get("status")
            for evse in evses
        ]
        charger_status = next(
            (status for status in connector_statuses if status),
            "UNKNOWN"
        )

    return {
        "id": charger_id,
        "status": charger_status
    }

@app.route("/chargers")
def get_chargers():
    now = time.time()

    if cache["data"] and now - cache["timestamp"] < CACHE_DURATION:
        return jsonify(cache["data"])

    results = []

    for cid in CHARGER_IDS:
        try:
            results.append(fetch_charger_status(cid))
        except Exception as exc:
            app.logger.exception("Failed to fetch charger %s", cid)
            results.append({
                "id": cid,
                "status": "ERROR",
                "error": str(exc)
            })

    cache["data"] = results
    cache["timestamp"] = now

    return jsonify(results)


@app.route("/chargers/debug")
def get_chargers_debug():
    results = []

    for cid in CHARGER_IDS:
        try:
            results.append(fetch_charger_status(cid))
        except Exception as exc:
            results.append({
                "id": cid,
                "status": "ERROR",
                "error": str(exc),
                "url": BASE_URL + str(cid)
            })

    return jsonify(results)

@app.route("/")
def serve_html():
    return send_from_directory(
        os.path.dirname(__file__),
        "check_charger.html"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
