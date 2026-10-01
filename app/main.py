import os
import sys
import time
import socket
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# logger aufsetzen
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("resilience-lab")

app = FastAPI(title="Resilience Lab API", version=os.getenv("APP_VERSION", "1.0.0"))
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

START_TIME = time.time()
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_ENV = os.getenv("APP_ENV", "production")

# zustände für die tests im speicher halten
LAB_STATE = {
    "is_live": True,
    "is_ready": True,
    "simulate_hang": False,
    "custom_delay_seconds": 0.0
}

class Order(BaseModel):
    id: str
    title: str
    status: str
    created_at: str
    processed_by_pod: str

# dummy daten
ORDERS: List[dict] = [
    {
        "id": "ORD-1001",
        "title": "Monatsbericht Q3",
        "status": "COMPLETED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "processed_by_pod": socket.gethostname()
    }
]

def get_pod_metadata():
    hostname = socket.gethostname()
    pod_ip = "127.0.0.1"
    try:
        pod_ip = socket.gethostbyname(hostname)
    except Exception:
        pass
    
    uptime = int(time.time() - START_TIME)
    return {
        "pod_name": os.getenv("POD_NAME", hostname),
        "pod_namespace": os.getenv("POD_NAMESPACE", "default"),
        "node_name": os.getenv("NODE_NAME", "local-node"),
        "pod_ip": pod_ip,
        "app_version": APP_VERSION,
        "environment": APP_ENV,
        "uptime_seconds": uptime,
        "uptime_formatted": f"{uptime // 60}m {uptime % 60}s",
        "is_live": LAB_STATE["is_live"],
        "is_ready": LAB_STATE["is_ready"],
        "simulate_hang": LAB_STATE["simulate_hang"]
    }

# middleware für latenz und künstliche hänger
@app.middleware("http")
async def handle_request_timing(request: Request, call_next):
    # falls hänger aktiviert, blockieren wir absichtlich
    if LAB_STATE["simulate_hang"] and request.url.path not in ["/lab/reset", "/lab/status"]:
        time.sleep(30)
    
    if LAB_STATE["custom_delay_seconds"] > 0:
        time.sleep(LAB_STATE["custom_delay_seconds"])

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    response.headers["X-Served-By-Pod"] = os.getenv("POD_NAME", socket.gethostname())
    return response

# web dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "meta": get_pod_metadata(),
        "orders": ORDERS[-10:],
        "lab": LAB_STATE
    })

# pod info json
@app.get("/api/info")
async def api_info():
    return JSONResponse(content={
        "status": "ok",
        "data": get_pod_metadata(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# aufträge auflisten
@app.get("/api/orders")
async def list_orders():
    return JSONResponse(content={"orders": ORDERS[-20:]})

# neuen testauftrag anlegen
@app.post("/api/orders")
async def create_order(title: Optional[str] = "Neuer Berechnungsauftrag"):
    order = {
        "id": f"ORD-{len(ORDERS) + 1001}",
        "title": title,
        "status": "PROCESSING",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "processed_by_pod": os.getenv("POD_NAME", socket.gethostname())
    }
    ORDERS.append(order)
    return JSONResponse(content=order, status_code=status.HTTP_201_CREATED)

# liveness probe
@app.get("/health/live")
async def liveness_probe():
    if not LAB_STATE["is_live"] or LAB_STATE["simulate_hang"]:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="deadlock")
    return {"status": "alive", "pod": os.getenv("POD_NAME", socket.gethostname())}

# readiness probe
@app.get("/health/ready")
async def readiness_probe():
    if not LAB_STATE["is_ready"]:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="not ready")
    return {"status": "ready", "pod": os.getenv("POD_NAME", socket.gethostname())}

# status vom labor abfragen
@app.get("/lab/status")
async def lab_status():
    return JSONResponse(content={"state": LAB_STATE, "meta": get_pod_metadata()})

# prozess crashen lassen
@app.post("/lab/crash")
async def trigger_crash():
    def exit_now():
        time.sleep(0.1)
        os._exit(1)
    
    import threading
    threading.Thread(target=exit_now, daemon=True).start()
    return JSONResponse(content={"message": "prozess wird beendet"})

# readiness toggeln
@app.post("/lab/toggle-ready")
async def toggle_ready():
    LAB_STATE["is_ready"] = not LAB_STATE["is_ready"]
    return JSONResponse(content={"is_ready": LAB_STATE["is_ready"]})

# deadlock simulieren
@app.post("/lab/simulate-hang")
async def simulate_hang():
    LAB_STATE["simulate_hang"] = True
    LAB_STATE["is_live"] = False
    return JSONResponse(content={"status": "deadlock"})

# alles wieder auf normal stellen
@app.post("/lab/reset")
async def reset_lab():
    LAB_STATE["is_live"] = True
    LAB_STATE["is_ready"] = True
    LAB_STATE["simulate_hang"] = False
    LAB_STATE["custom_delay_seconds"] = 0.0
    return JSONResponse(content={"status": "reset", "state": LAB_STATE})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
