import threading
from datetime import datetime, timezone
from typing import Dict, Any

from soft_sensor import predict_current_ph
from database import (
    db_log_heater, db_log_liquid, db_log_environment,
    db_log_tvoc, db_log_ethanol, db_log_predicted_ph
)

SYSTEM_STATE: Dict[str, Any] = {}
state_lock = threading.Lock()

def initialize_node_state(mac_address: str):
    """
    Initializes the default nested dictionary structure for a new node,
    replacing historical deques with a cache for the last logged metrics.
    """
    if mac_address not in SYSTEM_STATE:
        SYSTEM_STATE[mac_address] = {
            "metrics": {},
            "batch": {
                "active": False,
                "id": None,
                "db_batch_id": None,
                "start_time": None,
                "target_temp": 24.0,
                "predicted_ph": 4.5,
                "ph_start": 4.5,
                "ph_offset": 0.0,
                "volume_ml": 0.0,
                "sugar_g": 0.0,
                "culture_mass_g": 0.0,
                "t_min_hours": 0.0,
                "t_max_hours": 0.0,
                "t_desired_hours": 0.0,
                "last_bounds_update": 0.0,
            },
            "last_seen": None,
            "last_logged_metrics": {},  # Cache for CoV deadband filtering
        }

def telemetry_update_handler(mac_address: str, metric_name: str, value: float):
    """
    Implements a multi-rate, event-driven Change-of-Value (CoV) deadband
    filter to route sensor signals into the 7-table database schema.
    """
    with state_lock:
        initialize_node_state(mac_address)
        node_state = SYSTEM_STATE[mac_address]
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        node_state["metrics"][metric_name] = value
        node_state["last_seen"] = now

        batch_state = node_state.get("batch", {})
        if not batch_state.get("active") or not batch_state.get("start_time"):
            return

        db_batch_id = batch_state.get("db_batch_id")
        if db_batch_id is None:
            return

        elapsed_hours = (now - batch_state["start_time"]).total_seconds() / 3600.0
        last_log = node_state["last_logged_metrics"]
        metrics = node_state["metrics"]

        # Heater Group (Bed & Surface Temps)
        if metric_name in ('bed_temp_c', 'surface_temp_c'):
            current_val = metrics.get(metric_name)
            last_val = last_log.get(metric_name)
            if last_val is None or abs(current_val - last_val) >= 0.15:
                db_log_heater(db_batch_id, elapsed_hours, metrics.get('bed_temp_c'), metrics.get('surface_temp_c'))
                last_log['bed_temp_c'] = metrics.get('bed_temp_c')
                last_log['surface_temp_c'] = metrics.get('surface_temp_c')

        # Liquid Temp & Dependent Predicted pH Group
        elif metric_name == 'liquid_temp_c':
            # Always run soft sensor on new liquid temp
            predicted = predict_current_ph(
                ph_start=batch_state["ph_start"],
                start_time_epoch=batch_state["start_time"].timestamp(),
                current_temp=value
            )
            current_ph = predicted + batch_state.get("ph_offset", 0.0)
            batch_state["predicted_ph"] = current_ph
            
            # Deadband check for liquid temp
            last_liquid = last_log.get('liquid_temp_c')
            if last_liquid is None or abs(value - last_liquid) >= 0.05:
                db_log_liquid(db_batch_id, elapsed_hours, value, batch_state.get('target_temp'))
                last_log['liquid_temp_c'] = value

            # Deadband check for derived pH
            last_ph = last_log.get('predicted_ph')
            if last_ph is None or abs(current_ph - last_ph) >= 0.010:
                db_log_predicted_ph(db_batch_id, elapsed_hours, current_ph)
                last_log['predicted_ph'] = current_ph

        # Environment Group
        elif metric_name in ('ambient_temp_c', 'ambient_humid_pct'):
            current_val = metrics.get(metric_name)
            last_val = last_log.get(metric_name)
            if last_val is None or abs(current_val - last_val) >= 0.20:
                db_log_environment(db_batch_id, elapsed_hours, metrics.get('ambient_temp_c'), metrics.get('ambient_humid_pct'))
                last_log['ambient_temp_c'] = metrics.get('ambient_temp_c')
                last_log['ambient_humid_pct'] = metrics.get('ambient_humid_pct')

        # TVOC
        elif metric_name == 'digital_tvoc_ppm':
            last_val = last_log.get('digital_tvoc_ppm')
            if last_val is None or abs(value - last_val) >= 0.50:
                db_log_tvoc(db_batch_id, elapsed_hours, value)
                last_log['digital_tvoc_ppm'] = value
        
        # Ethanol
        elif metric_name == 'analog_ethanol_ppm':
            last_val = last_log.get('analog_ethanol_ppm')
            if last_val is None or abs(value - last_val) >= 0.25:
                db_log_ethanol(db_batch_id, elapsed_hours, value)
                last_log['analog_ethanol_ppm'] = value