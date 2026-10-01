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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("resilience-lab")

app = FastAPI(title="Resilience Lab API", version=os.getenv("APP_VERSION", "1.0.0"))

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Startzeitpunkt
START_TIME = time.time()
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_ENVIRONMENT = os.getenv("APP_ENV", "production")

# Zustände für Fehlerinduktion (In-Memory pro Pod)
LAB_STATE = {
    "is_live": True,
    "is_ready": True,
    "simulate_hang": False,
    "crash_count": 0,
    "custom_delay_seconds": 0.0
}

# Simulierte In-Memory-Aufträge (Order Processing)
class Order(BaseModel):
    id: str
    title: str
    status: str
    created_at: str
    processed_by_pod: str

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
    
    uptime_seconds = int(time.time() - START_TIME)
    return {
        "pod_name": os.getenv("POD_NAME", hostname),
        "pod_namespace": os.getenv("POD_NAMESPACE", "default"),
        "node_name": os.getenv("NODE_NAME", "local-node"),
        "pod_ip": pod_ip,
        "app_version": APP_VERSION,
        "environment": APP_ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
        "uptime_formatted": f"{uptime_seconds // 60}m {uptime_seconds % 60}s",
        "is_live": LAB_STATE["is_live"],
        "is_ready": LAB_STATE["is_ready"],
        "simulate_hang": LAB_STATE["simulate_hang"]
    }

@app.middleware("http")
async def add_timing_and_hang_middleware(request: Request, call_next):
    # Bei aktiviertem Hang-Zustand blockieren (für Liveness-Ausfall)
    if LAB_STATE["simulate_hang"] and request.url.path not in ["/lab/reset", "/lab/status"]:
        logger.warning("Pod befindet sich im simulierten Hänger/Deadlock!")
        time.sleep(30)
    
    if LAB_STATE["custom_delay_seconds"] > 0:
        time.sleep(LAB_STATE["custom_delay_seconds"])

    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    response.headers["X-Served-By-Pod"] = os.getenv("POD_NAME", socket.gethostname())
    return response

# --- Web-Dashboard ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    metadata = get_pod_metadata()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "meta": metadata,
        "orders": ORDERS[-10:],
        "lab": LAB_STATE
    })

# --- JSON Info API ---
@app.get("/api/info")
async def api_info():
    metadata = get_pod_metadata()
    return JSONResponse(content={
        "status": "ok",
        "data": metadata,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# --- Order Processing API (Fachlicher Praxisfall) ---
@app.get("/api/orders")
async def list_orders():
    return JSONResponse(content={"orders": ORDERS[-20:]})

@app.post("/api/orders")
async def create_order(title: Optional[str] = "Neuer Berechnungsauftrag"):
    new_order = {
        "id": f"ORD-{len(ORDERS) + 1001}",
        "title": title,
        "status": "PROCESSING",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "processed_by_pod": os.getenv("POD_NAME", socket.gethostname())
    }
    ORDERS.append(new_order)
    logger.info(f"Auftrag {new_order['id']} von Pod {new_order['processed_by_pod']} erstellt.")
    return JSONResponse(content=new_order, status_code=status.HTTP_201_CREATED)

# --- Kubernetes Health Probes ---
@app.get("/health/live")
async def liveness_probe():
    """Liveness Probe: Prüft, ob der Container-Prozess noch responsiv ist."""
    if not LAB_STATE["is_live"] or LAB_STATE["simulate_hang"]:
        logger.error("Liveness-Probe fehlgeschlagen!")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Liveness check failed")
    return {"status": "alive", "pod": os.getenv("POD_NAME", socket.gethostname())}

@app.get("/health/ready")
async def readiness_probe():
    """Readiness Probe: Steuert, ob der Pod Traffic vom Service erhalten darf."""
    if not LAB_STATE["is_ready"]:
        logger.warning("Readiness-Probe meldet UNREADY!")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Pod is not ready for traffic")
    return {"status": "ready", "pod": os.getenv("POD_NAME", socket.gethostname())}

# --- Geschütztes Fault-Injection-Labor (Experimente) ---
@app.get("/lab/status")
async def lab_status():
    return JSONResponse(content={"state": LAB_STATE, "meta": get_pod_metadata()})

@app.post("/lab/crash")
async def trigger_crash():
    """Experiment 1: Simuliert einen abrupten Prozessabsturz."""
    logger.critical("FORCIERTER PROZESSABSTURZ ausgelöst über /lab/crash!")
    # Kurz verzögern, damit Response gesendet werden kann, dann Exit
    def do_exit():
        time.sleep(0.1)
        os._exit(1)
    
    import threading
    threading.Thread(target=do_exit, daemon=True).start()
    return JSONResponse(content={
        "action": "crash_initiated",
        "message": f"Pod {socket.gethostname()} beendet Prozess sofort mit Exit-Code 1."
    })

@app.post("/lab/toggle-ready")
async def toggle_ready():
    """Experiment 2 Vorstufe: Schaltet Readiness um."""
    LAB_STATE["is_ready"] = not LAB_STATE["is_ready"]
    logger.info(f"Readiness umgeschaltet auf: {LAB_STATE['is_ready']}")
    return JSONResponse(content={"is_ready": LAB_STATE["is_ready"]})

@app.post("/lab/simulate-hang")
async def simulate_hang():
    """Optionales Experiment: Simuliert Deadlock/Hänger (triggert Liveness-Fehlschlag)."""
    LAB_STATE["simulate_hang"] = True
    LAB_STATE["is_live"] = False
    logger.error("Simulierter Deadlock aktiviert! Anfragen werden blockiert.")
    return JSONResponse(content={"status": "deadlock_simulated"})

@app.post("/lab/reset")
async def reset_lab():
    LAB_STATE["is_live"] = True
    LAB_STATE["is_ready"] = True
    LAB_STATE["simulate_hang"] = False
    LAB_STATE["custom_delay_seconds"] = 0.0
    logger.info("Labor-Zustand zurückgesetzt.")
    return JSONResponse(content={"status": "reset_successful", "state": LAB_STATE})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
