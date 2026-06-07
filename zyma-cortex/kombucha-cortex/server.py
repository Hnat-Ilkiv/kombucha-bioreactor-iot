import asyncio, math
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from mqtt_manager import MQTTManager
from state import SYSTEM_STATE, state_lock, telemetry_update_handler, initialize_node_state
from workers import state_verification_worker, calculate_batch_time_bounds
from ui_base import BASE_HTML
from ui_nodes import get_nodes_table_html
from ui_dashboard import get_node_dashboard_html
from ui_telemetry import get_node_stats_html
from ui_history_sidebar import get_history_sidebar_html
from ui_history_view import get_history_page_html, get_historical_dashboard_html
from ui_controls import get_control_panel_html
from database import (
    db_start_new_batch, db_stop_active_batch, db_save_calibration_offset, init_sqlite_db,
    db_get_all_batches, db_get_batch_by_id, db_get_batch_telemetry
)

app = FastAPI(title="Kombucha Cortex: MPC Router")

@app.on_event("startup")
async def startup_event():
    init_sqlite_db()
    app.state.mqtt = MQTTManager(on_telemetry_received=telemetry_update_handler)
    app.state.mqtt.connect()
    asyncio.create_task(state_verification_worker(app.state.mqtt))

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "mqtt"): app.state.mqtt.client.loop_stop()

def _recalculate_target_temp(ph_start: float, t_desired_hours: float) -> float:
    """Helper to run the inverse MPC model to find the required target temperature."""
    t_des_min = t_desired_hours * 60.0
    if t_des_min <= 0 or ph_start <= 2.5: return 22.0
    k_req = - (1.0 / t_des_min) * math.log(1.1 / (ph_start - 2.5))
    target_temp = (k_req * 24.0) / 0.00014
    return max(18.0, min(29.0, target_temp))

@app.get("/", response_class=HTMLResponse)
async def get_root(): return BASE_HTML

@app.get("/api/ui/nodes_table", response_class=HTMLResponse)
async def get_nodes_table():
    with state_lock: return get_nodes_table_html(SYSTEM_STATE)

@app.get("/api/ui/node/{mac}/dashboard", response_class=HTMLResponse)
async def get_dashboard(mac: str):
    with state_lock: return get_node_dashboard_html(mac.upper(), SYSTEM_STATE.get(mac.upper(), {}))

@app.get("/api/ui/node/{mac}/stats", response_class=HTMLResponse)
async def get_stats(mac: str):
    with state_lock: return get_node_stats_html(mac.upper(), SYSTEM_STATE.get(mac.upper(), {}))

def _format_chart_data(batch, telemetry: dict) -> dict:
    """
    Helper to format telemetry data into a standardized chart JSON response.
    Natively supports both Python 'dict' (active batch) and 'sqlite3.Row' (historical batch).
    """
    temps_liquid = telemetry.get("temps_liquid", [])
    all_x_values = [item["x"] for item in temps_liquid if isinstance(item, dict) and "x" in item]

    if isinstance(batch, dict):  # Active running process
        t_max = batch.get("t_max_hours") or batch.get("t_desired_hours", 120)
        if all_x_values:
            t_max = max(max(all_x_values), t_max)
    else:  # Historical batch row from sqlite3.Row
        t_max = max(all_x_values) if all_x_values else batch["t_desired_hours"]
    
    return {
        "t_max": t_max,
        "temps_liquid": temps_liquid,
        "temp_target": telemetry.get("temp_target", []),
        "temps_bed": telemetry.get("temps_bed", []),
        "temps_surface": telemetry.get("temps_surface", []),
        "phs": telemetry.get("phs", []),
        "gases_ethanol": telemetry.get("gases_ethanol", []),
        "gases_tvoc_ppm": telemetry.get("gases_tvoc_ppm") or telemetry.get("gases_tvoc", []),
    }

@app.get("/api/ui/node/{mac}/chart_data", response_class=JSONResponse)
async def get_chart_data(mac: str):
    with state_lock:
        node_state = SYSTEM_STATE.get(mac.upper(), {})
        batch = node_state.get("batch", {})
        db_batch_id = batch.get("db_batch_id")

        if batch.get("active") and db_batch_id is not None:
            telemetry = db_get_batch_telemetry(db_batch_id)
            return JSONResponse(_format_chart_data(batch, telemetry))
    
    # Default empty response if no active batch
    return JSONResponse({
        "t_max": 120, "temps_liquid": [], "temp_target": [], "temps_bed": [],
        "temps_surface": [], "phs": [], "gases_ethanol": [], "gases_tvoc_ppm": []
    })

@app.get("/api/ui/history_sidebar", response_class=HTMLResponse)
async def get_history_sidebar():
    batches = db_get_all_batches()
    return get_history_sidebar_html(batches)

@app.get("/api/ui/history", response_class=HTMLResponse)
async def get_history_page():
    batches = db_get_all_batches()
    return get_history_page_html(batches)

@app.get("/api/ui/history/batch/{batch_id}/view", response_class=HTMLResponse)
async def get_historical_batch_view(batch_id: int):
    batch = db_get_batch_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return get_historical_dashboard_html(batch)

@app.get("/api/ui/history/batch/{batch_id}/chart_data", response_class=JSONResponse)
async def get_historical_chart_data(batch_id: int):
    batch = db_get_batch_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    telemetry = db_get_batch_telemetry(batch_id)
    return JSONResponse(_format_chart_data(batch, telemetry))

@app.post("/api/control/{mac}/start", response_class=HTMLResponse)
async def post_start(mac: str, request: Request, ph_start: float = Form(...), volume_ml: float = Form(0.0), sugar_g: float = Form(0.0), culture_mass_g: float = Form(0.0)):
    mac = mac.upper()
    with state_lock:
        initialize_node_state(mac)
        node_state = SYSTEM_STATE[mac]
        
        t_ambient = node_state.get("metrics", {}).get("ambient_temp_c", 22.0)
        t_min, t_max = calculate_batch_time_bounds(ph_start, t_ambient)
        t_desired = (t_min + t_max) / 2.0
        target_temp = _recalculate_target_temp(ph_start, t_desired)

        db_batch_id = db_start_new_batch(mac, volume_ml, sugar_g, culture_mass_g, ph_start, target_temp, t_desired)
        
        node_state["last_logged_metrics"] = {}
        node_state["batch"] = {
            "active": True, "id": db_batch_id, "db_batch_id": db_batch_id, "target_temp": target_temp, "ph_start": ph_start,
            "predicted_ph": ph_start, "ph_offset": 0.0, "t_min_hours": t_min, "t_max_hours": t_max, "t_desired_hours": t_desired,
            "start_time": datetime.now(timezone.utc).replace(tzinfo=None), "volume_ml": volume_ml,
            "sugar_g": sugar_g, "culture_mass_g": culture_mass_g, "last_db_write_time": None
        }

        request.app.state.mqtt.send_target_temperature(mac, target_temp)
        request.app.state.mqtt.send_run_state(mac, True)
        return get_node_dashboard_html(mac, node_state)

@app.post("/api/control/{mac}/stop", response_class=HTMLResponse)
async def post_stop(mac: str, request: Request):
    mac = mac.upper()
    with state_lock:
        node_state = SYSTEM_STATE.get(mac, {})
        if node_state and node_state.get("batch", {}).get("active"):
            db_stop_active_batch(mac)
            node_state["batch"]["active"] = False
        return get_node_dashboard_html(mac, node_state)

@app.post("/api/control/{mac}/adjust_deadline", response_class=HTMLResponse)
async def post_adjust_deadline(mac: str, request: Request, t_desired_hours: float = Form(...)):
    mac = mac.upper()
    with state_lock:
        node_state = SYSTEM_STATE.get(mac, {})
        if node_state and node_state.get("batch", {}).get("active"):
            batch = node_state["batch"]
            batch["t_desired_hours"] = t_desired_hours
            new_target_temp = _recalculate_target_temp(batch["ph_start"], t_desired_hours)
            batch["target_temp"] = new_target_temp
            request.app.state.mqtt.send_target_temperature(mac, new_target_temp)
        return get_node_dashboard_html(mac, node_state)

@app.post("/api/control/{mac}/calibrate", response_class=HTMLResponse)
async def post_calibrate(mac: str, manual_ph: float = Form(...), precision_level: str = Form(...)):
    mac = mac.upper()
    with state_lock:
        node_state = SYSTEM_STATE.get(mac, {})
        if node_state and "batch" in node_state and "predicted_ph" in node_state["batch"]:
            K = 1.0 if precision_level == "digital" else 0.3
            delta = manual_ph - node_state["batch"]["predicted_ph"]
            
            if "ph_offset" not in node_state["batch"]:
                node_state["batch"]["ph_offset"] = 0.0

            node_state["batch"]["ph_offset"] += K * delta
            node_state["batch"]["predicted_ph"] += K * delta
            db_save_calibration_offset(mac, node_state["batch"]["ph_offset"])
        return get_node_dashboard_html(mac, node_state)

