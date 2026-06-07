# config.py
# Єдине джерело істини для інтерфейсів комунікації Zyma CPS

# Адреса твого віддаленого брокера на RPi3B (зміни IP, якщо він інший у локальній мережі)
MQTT_BROKER_HOST = "192.168.0.201" 
MQTT_BROKER_PORT = 1883
MQTT_CLIENT_ID = "zyma-core-laptop"

# Специфікація безпеки технологічного процесу
MIN_SAFE_TEMP = 18.0
MAX_SAFE_TEMP = 29.0

# Карта вхідних топіків телеметрії від ESP32 (Hub Subs)
TOPICS_TELEMETRY = {
    "bed_temp_c": "sensors/bed_temp_c",
    "surface_temp_c": "sensors/surface_temp_c",
    "liquid_temp_c": "sensors/liquid_temp_c",
    "ambient_temp_c": "sensors/ambient_temp_c",
    "ambient_humid_pct": "sensors/ambient_humid_pct",
    "digital_tvoc_ppm": "sensors/digital_tvoc_ppm",
    "analog_ethanol_ppm": "sensors/analog_ethanol_ppm",
    "heater_power_pct": "sensors/heater_power_pct",
    "process_state": "sensors/process_state",
    "status": "system/status",
    "debug": "system/debug"
}

# Карта вихідних топіків керування на ESP32 (Hub Pubs)
TOPICS_CONTROL = {
    "run_set": "control/run_set",          # Приймає "0" або "1"
    "target_set": "control/target_set"    # Приймає "18" - "29"
}