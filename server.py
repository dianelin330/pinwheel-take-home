"""Run python3 server.py for the local dashboard with forecasts."""
import csv
import json
from dataclasses import asdict
from datetime import date
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from forecasting import CSVEmploymentSource, ExponentialSmoothingForecaster
ROOT = Path(__file__).resolve().parent

def forecast_payload():
    source = CSVEmploymentSource()
    model = ExponentialSmoothingForecaster(source)
    with source.path.open(newline="") as stream:
        keys = sorted({(r["agg_RIS"], r["category"]) for r in csv.DictReader(stream) if r["timestep"] == "M"})
    return [asdict(model.forecast(group, category)) for group, category in keys]

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path != "/api/forecasts":
            return super().do_GET()
        try:
            body = json.dumps(forecast_payload(), default=lambda v: v.isoformat() if isinstance(v, date) else v).encode()
            self.send_response(200)
        except (ValueError, OSError) as error:
            body = json.dumps({"error": str(error)}).encode()
            self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    print("Employment explorer: http://127.0.0.1:8001", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8001), partial(Handler, directory=str(ROOT))).serve_forever()
