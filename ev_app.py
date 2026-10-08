from flask import Flask, jsonify, request, send_from_directory
import requests
import os
import time

app = Flask(__name__)

# Explicit charger order
CHARGER_IDS = [1389, 1391, 3232, 3233]

CHARGE_POINT_IDS = {3232: 2398, 3233: 4206, 1389: 4095, 1391: 4002}
CHARGER_URLS = {
    cid: f"https://adhoc.ev-plus.com/2/tenant/ev_ev_passport_operator/cp/{cp}/charge-point"
    for cid, cp in CHARGE_POINT_IDS.items()
}

BASE_URL = "https://adhoc.ev-plus.com/api/v1/charge-points"

# Cache setup
cache = {
    "data": None,
    "timestamp": 0
}
CACHE_DURATION = 30  # seconds

# Custom headers
HEADERS = {
    "Tenant": "ev_ev_passport_operator",
    "Cache-Control": "no-cache",
    "User-Agent": (
        "EV-Dashboard/1.0 "
        "UChicago CS PhD student tired of clicking through multiple links just to see if a charger is available"
    )
}


def parse_charger_status(data, charger_id):
    charge_point = data["chargePoint"]
    evse = next(
        (evse for evse in data["evses"]
         if str(evse.get("physicalReference")) == str(charger_id)),
        None
    )
    if evse is None:
        raise ValueError(f"EV Plus response has no EVSE for charger {charger_id}")

    network_status = charge_point.get("networkStatus")
    if network_status and network_status != "available":
        return "UNAVAILABLE"
    if charge_point.get("status") != "active" or evse.get("status") != "enabled":
        return "UNAVAILABLE"

    # Network availability and enabled connectors do not imply an idle charger.
    hardware_status = evse.get("hardwareStatus")
    statuses = {
        "available": "AVAILABLE", "charging": "CHARGING",
        "preparing": "PREPARING", "finishing": "FINISHING",
        "occupied": "IN_USE", "reserved": "RESERVED",
        "faulted": "FAULTED", "unavailable": "UNAVAILABLE",
        "suspendedEV": "SUSPENDED_EV", "suspendedEVSE": "SUSPENDED_EVSE",
    }
    return statuses.get(hardware_status, "UNKNOWN")


def fetch_charger_status(charger_id):
    response = requests.get(
        BASE_URL,
        params={"chargePointId": CHARGE_POINT_IDS[charger_id]},
        headers={**HEADERS, "tenant-path": CHARGER_URLS[charger_id]},
        timeout=5
    )
    response.raise_for_status()
    data = response.json()["data"]
    if data["chargePoint"]["id"] != CHARGE_POINT_IDS[charger_id]:
        raise ValueError("EV Plus returned a different charge point")
    charger_status = parse_charger_status(data, charger_id)

    return {
        "id": charger_id,
        "status": charger_status,
        "url": CHARGER_URLS[charger_id]
    }

@app.route("/chargers")
def get_chargers():
    now = time.time()

    if request.args.get("refresh") != "1" and cache["data"] and now - cache["timestamp"] < CACHE_DURATION:
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
                "url": CHARGER_URLS[cid],
                "error": str(exc)
            })

    cache["data"] = results
    cache["timestamp"] = time.time()

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
                "url": CHARGER_URLS[cid],
                "error": str(exc),
                "statusUrl": f"{BASE_URL}?chargePointId={CHARGE_POINT_IDS[cid]}"
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
