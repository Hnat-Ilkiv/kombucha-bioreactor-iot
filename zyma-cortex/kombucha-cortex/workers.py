import asyncio
import logging
import math
import time
from datetime import datetime

# Use flat absolute imports for local modules
from state import SYSTEM_STATE, state_lock
from mqtt_manager import MQTTManager
from soft_sensor import calculate_k_coefficient # This is now unused, but keeping it to avoid breaking other files if they depend on it

# Configure basic logging for worker events
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def calculate_batch_time_bounds(ph_start: float, t_ambient: float) -> tuple[float, float]:
    """
    Calculates the min and max fermentation time bounds, with internal calculations
    performed in minutes for precision and final output converted to hours.
    Includes thermodynamic smooth clamping to prevent runaway time estimates.
    """
    if ph_start <= 2.5:
        return (0.0, 0.0)
    
    log_num = math.log(1.1 / (ph_start - 2.5))
    
    # t_min is constant, based on max metabolic rate
    t_min_minutes = - (1.0 / 0.00022) * log_num

    # t_max is based on ambient temperature, with protective clamping
    t_ambient_clamped = max(15.0, t_ambient) # Clamped to 15.0 as per new requirement
    k_ambient = 0.00014 * (t_ambient_clamped / 24.0) # Directly use simplified formula
    
    t_max_minutes = float("inf")
    if k_ambient > 0:
        t_max_minutes = - (1.0 / k_ambient) * log_num

    t_min_hours = round(t_min_minutes / 60.0, 1)
    t_max_hours = round(t_max_minutes / 60.0, 1) if t_max_minutes != float("inf") else float("inf")
    
    return (t_min_hours, t_max_hours)

def _recalculate_target_temp(ph_start: float, t_desired_hours: float) -> float:
    """Helper to run the inverse MPC model to find the required target temperature."""
    t_des_min = t_desired_hours * 60.0
    if t_des_min <= 0 or ph_start <= 2.5: return 22.0
    k_req = - (1.0 / t_des_min) * math.log(1.1 / (ph_start - 2.5))
    target_temp = (k_req * 24.0) / 0.00014
    return max(18.0, min(29.0, target_temp))


async def state_verification_worker(mqtt_manager: MQTTManager):
    """
    Continuously verifies desired vs. actual state, re-sends commands,
    and enforces safety overrides. Target temperatures and time bounds are
    now calculated only at batch start or on manual adjustment.
    """
    while True:
        await asyncio.sleep(10)
        if mqtt_manager is None:
            continue

        with state_lock:
            # Use a copy of keys to allow for safe modification of the dictionary during iteration
            mac_keys = list(SYSTEM_STATE.keys())
            for mac in mac_keys:
                # Sanitize node MAC to strip problematic characters for URL/topic safety
                sanitized_mac = mac.replace("$", "").replace("%24", "")
                
                node_state = SYSTEM_STATE.get(mac)
                if not node_state: continue

                if mac != sanitized_mac:
                    # If sanitization occurred, update the state dictionary to use the clean key
                    SYSTEM_STATE[sanitized_mac] = SYSTEM_STATE.pop(mac)
                
                batch = node_state.get("batch", {})
                metrics = node_state.get("metrics", {})

                # Split logic for active vs. inactive batches
                if batch.get("active"):
                    # --- ACTIVE BATCH LOGIC ---
                    # Throttled (5-minute) block for expensive ambient-based MPC calculations
                    if time.time() - batch.get("last_bounds_update", 0) > 300:
                        logging.info(f"[{sanitized_mac}] Running 5-minute throttled MPC update.")
                        t_ambient = metrics.get("ambient_temp_c", 22.0)
                        t_min_h, t_max_h = calculate_batch_time_bounds(batch["ph_start"], t_ambient)
                        batch["t_min_hours"] = t_min_h
                        batch["t_max_hours"] = t_max_h
                        
                        new_target_temp = _recalculate_target_temp(batch["ph_start"], batch["t_desired_hours"])
                        batch["target_temp"] = new_target_temp
                        batch["last_bounds_update"] = time.time()

                    # Desired vs. Actual State Verification (runs every 10s)
                    desired_run_state = batch.get("active", False)
                    actual_run_state = metrics.get("process_state")
                    is_mismatch = (desired_run_state and actual_run_state != 1.0) # Check for desired active but actual inactive

                    if actual_run_state is not None and is_mismatch:
                        logging.warning(f"State mismatch for {sanitized_mac}: Re-aligning run state.")
                        mqtt_manager.send_run_state(sanitized_mac, desired_run_state)

                    desired_temp = batch.get("target_temp")
                    actual_temp_setpoint = metrics.get("target_set")
                    if actual_temp_setpoint is not None and abs(actual_temp_setpoint - desired_temp) > 0.1:
                        logging.warning(f"State mismatch for {sanitized_mac}: Re-aligning target temp from {actual_temp_setpoint} to {desired_temp}.")
                        mqtt_manager.send_target_temperature(sanitized_mac, desired_temp)

                    # Shift-Control Safety Override
                    predicted_ph = batch.get("predicted_ph")
                    if predicted_ph is not None and predicted_ph <= 3.6:
                        logging.critical(f"SAFETY OVERRIDE for {sanitized_mac}: Predicted pH ({predicted_ph:.3f}) is <= 3.6. Stopping batch.")
                        mqtt_manager.send_run_state(sanitized_mac, False)
                        batch["active"] = False
                        logging.info(f"Batch for node {sanitized_mac} has been deactivated by safety override.")
                else:
                    # --- INACTIVE BATCH LOGIC ---
                    # Force physical deactivation if hardware is still running when it should not be
                    if metrics.get("process_state") == 1.0:
                        logging.critical(f"ZOMBIE HEATER DETECTED on {sanitized_mac}: Process state is {metrics.get('process_state')}. Forcing deactivation.")
                        mqtt_manager.send_run_state(sanitized_mac, False)
