# EV Charger Dashboard

Open the dashboard through its Flask server so it can load live charger statuses. Double-clicking `check_charger.html` will not load those statuses.

## Open the dashboard

In Terminal, run:

```sh
cd ~/Desktop/ev-dashboard
.venv/bin/python ev_app.py
```

Leave that Terminal window running, then open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

On macOS, you can also open the page from a second Terminal window:

```sh
open http://127.0.0.1:8000/
```

Press `Control+C` in the server's Terminal window to stop the dashboard. Run the same startup command whenever you want to use it again.

## "Address already in use"

The dashboard may already be running. Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) first; if the dashboard appears, you do not need to start another server.

If another application is using that address, run the dashboard on port 8001 instead:

```sh
cd ~/Desktop/ev-dashboard
.venv/bin/python -m flask --app ev_app run --port 8001
```

Then open [http://127.0.0.1:8001/](http://127.0.0.1:8001/).

## First-time setup

If `.venv` is missing, install Python 3 and run these commands before starting the dashboard:

```sh
cd ~/Desktop/ev-dashboard
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

An internet connection is needed to fetch charger statuses from EV Plus. Click a charger to open its charging page. Statuses refresh automatically every 30 seconds; **Refresh Status** fetches fresh data immediately, bypassing the server's 30-second cache.
