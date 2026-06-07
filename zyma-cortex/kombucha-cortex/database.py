import sqlite3
from datetime import datetime, timezone
from typing import Dict

DB_FILE = "kombucha_cortex.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn



def init_sqlite_db():
    """
    Initializes the database and creates the 7 normalized tables if they don't exist.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 1. Batches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT, device_mac TEXT NOT NULL,
                start_time TEXT NOT NULL, end_time TEXT, volume_ml REAL, sugar_g REAL,
                culture_mass_g REAL, ph_start REAL, ph_offset REAL DEFAULT 0.0,
                target_temp REAL, t_desired_hours REAL, is_active INTEGER DEFAULT 1
            )
        """)
        # 2. Heater Temp table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_heater_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL, elapsed_hours REAL NOT NULL,
                heater_temp REAL, surface_temp REAL,
                FOREIGN KEY (batch_id) REFERENCES batches (id)
            )
        """)
        # 3. Liquid Temp table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_liquid_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL, elapsed_hours REAL NOT NULL,
                liquid_temp REAL, target_temp REAL,
                FOREIGN KEY (batch_id) REFERENCES batches (id)
            )
        """)
        # 4. Environment table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_environment (
                id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL, elapsed_hours REAL NOT NULL,
                ambient_temp REAL, ambient_humid REAL,
                FOREIGN KEY (batch_id) REFERENCES batches (id)
            )
        """)
        # 5. TVOC table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_tvoc (
                id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL, elapsed_hours REAL NOT NULL, tvoc_ppm REAL,
                FOREIGN KEY (batch_id) REFERENCES batches (id)
            )
        """)
        # 6. Ethanol table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_ethanol (
                id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL, elapsed_hours REAL NOT NULL, ethanol_ppm REAL,
                FOREIGN KEY (batch_id) REFERENCES batches (id)
            )
        """)
        # 7. Predicted pH table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_predicted_ph (
                id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL, elapsed_hours REAL NOT NULL, predicted_ph REAL,
                FOREIGN KEY (batch_id) REFERENCES batches (id)
            )
        """)
        conn.commit()

def db_start_new_batch(mac: str, vol: float, sugar: float, mass: float, ph_start: float, target_temp: float, t_des: float) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        start_time_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO batches (device_mac, start_time, volume_ml, sugar_g, culture_mass_g, ph_start, target_temp, t_desired_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (mac, start_time_iso, vol, sugar, mass, ph_start, target_temp, t_des))
        conn.commit()
        return cursor.lastrowid

def db_stop_active_batch(mac: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        end_time_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("UPDATE batches SET is_active = 0, end_time = ? WHERE device_mac = ? AND is_active = 1", (end_time_iso, mac))
        conn.commit()

def db_save_calibration_offset(mac: str, new_offset: float):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE batches SET ph_offset = ? WHERE device_mac = ? AND is_active = 1", (new_offset, mac))
        conn.commit()

def db_log_heater(batch_id: int, hours: float, heater: float, surface: float):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO log_heater_temp (batch_id, timestamp, elapsed_hours, heater_temp, surface_temp) VALUES (?, ?, ?, ?, ?)",
                     (batch_id, datetime.now(timezone.utc).isoformat(), hours, heater, surface))
        conn.commit()

def db_log_liquid(batch_id: int, hours: float, liquid: float, target: float):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO log_liquid_temp (batch_id, timestamp, elapsed_hours, liquid_temp, target_temp) VALUES (?, ?, ?, ?, ?)",
                     (batch_id, datetime.now(timezone.utc).isoformat(), hours, liquid, target))
        conn.commit()

def db_log_environment(batch_id: int, hours: float, ambient: float, humid: float):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO log_environment (batch_id, timestamp, elapsed_hours, ambient_temp, ambient_humid) VALUES (?, ?, ?, ?, ?)",
                     (batch_id, datetime.now(timezone.utc).isoformat(), hours, ambient, humid))
        conn.commit()

def db_log_tvoc(batch_id: int, hours: float, tvoc: float):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO log_tvoc (batch_id, timestamp, elapsed_hours, tvoc_ppm) VALUES (?, ?, ?, ?)",
                     (batch_id, datetime.now(timezone.utc).isoformat(), hours, tvoc))
        conn.commit()

def db_log_ethanol(batch_id: int, hours: float, ethanol: float):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO log_ethanol (batch_id, timestamp, elapsed_hours, ethanol_ppm) VALUES (?, ?, ?, ?)",
                     (batch_id, datetime.now(timezone.utc).isoformat(), hours, ethanol))
        conn.commit()

def db_log_predicted_ph(batch_id: int, hours: float, ph: float):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO log_predicted_ph (batch_id, timestamp, elapsed_hours, predicted_ph) VALUES (?, ?, ?, ?)",
                     (batch_id, datetime.now(timezone.utc).isoformat(), hours, ph))
        conn.commit()

def db_get_heater_temp_logs(batch_id: int) -> list:
    with get_db_connection() as conn:
        return conn.execute("SELECT elapsed_hours, heater_temp, surface_temp FROM log_heater_temp WHERE batch_id = ? ORDER BY elapsed_hours ASC", (batch_id,)).fetchall()

def db_get_liquid_temp_logs(batch_id: int) -> list:
    with get_db_connection() as conn:
        return conn.execute("SELECT elapsed_hours, liquid_temp, target_temp FROM log_liquid_temp WHERE batch_id = ? ORDER BY elapsed_hours ASC", (batch_id,)).fetchall()

def db_get_tvoc_logs(batch_id: int) -> list:
    with get_db_connection() as conn:
        return conn.execute("SELECT elapsed_hours, tvoc_ppm FROM log_tvoc WHERE batch_id = ? ORDER BY elapsed_hours ASC", (batch_id,)).fetchall()

def db_get_ethanol_logs(batch_id: int) -> list:
    with get_db_connection() as conn:
        return conn.execute("SELECT elapsed_hours, ethanol_ppm FROM log_ethanol WHERE batch_id = ? ORDER BY elapsed_hours ASC", (batch_id,)).fetchall()

def db_get_predicted_ph_logs(batch_id: int) -> list:
    with get_db_connection() as conn:
        return conn.execute("SELECT elapsed_hours, predicted_ph FROM log_predicted_ph WHERE batch_id = ? ORDER BY elapsed_hours ASC", (batch_id,)).fetchall()

def db_get_all_batches() -> list:
    """
    Retrieves all batch records from the database, ordered by ID in descending order.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM batches ORDER BY id DESC")
        return cursor.fetchall()

def db_get_batch_by_id(batch_id: int) -> dict | None:
    """
    Retrieves a single batch record by its ID.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM batches WHERE id = ?", (batch_id,))
        return cursor.fetchone()

def db_get_batch_telemetry(batch_id: int) -> dict:
    """
    Retrieves all telemetry logs for a given batch_id, consolidating them into a single dictionary.
    """
    telemetry_data = {
        "temps_liquid": [], "temps_bed": [], "temps_surface": [], "phs": [],
        "gases_ethanol": [], "gases_tvoc": []
    }
    with get_db_connection() as conn:
        # Fetch liquid temperatures (includes target temp)
        liquid_logs = conn.execute("SELECT elapsed_hours, liquid_temp, target_temp FROM log_liquid_temp WHERE batch_id = ? ORDER BY elapsed_hours ASC", (batch_id,)).fetchall()
        telemetry_data["temps_liquid"] = [{"x": row["elapsed_hours"], "y": row["liquid_temp"]} for row in liquid_logs]
        telemetry_data["temp_target"] = [{"x": row["elapsed_hours"], "y": row["target_temp"]} for row in liquid_logs]

        # Fetch heater and surface temperatures
        heater_logs = conn.execute("SELECT elapsed_hours, heater_temp, surface_temp FROM log_heater_temp WHERE batch_id = ? ORDER BY elapsed_hours ASC", (batch_id,)).fetchall()
        telemetry_data["temps_bed"] = [{"x": row["elapsed_hours"], "y": row["heater_temp"]} for row in heater_logs]
        telemetry_data["temps_surface"] = [{"x": row["elapsed_hours"], "y": row["surface_temp"]} for row in heater_logs]

        # Fetch predicted pH
        ph_logs = conn.execute("SELECT elapsed_hours, predicted_ph FROM log_predicted_ph WHERE batch_id = ? ORDER BY elapsed_hours ASC", (batch_id,)).fetchall()
        telemetry_data["phs"] = [{"x": row["elapsed_hours"], "y": row["predicted_ph"]} for row in ph_logs]

        # Fetch ethanol
        ethanol_logs = conn.execute("SELECT elapsed_hours, ethanol_ppm FROM log_ethanol WHERE batch_id = ? ORDER BY elapsed_hours ASC", (batch_id,)).fetchall()
        telemetry_data["gases_ethanol"] = [{"x": row["elapsed_hours"], "y": row["ethanol_ppm"]} for row in ethanol_logs]

        # Fetch TVOC
        tvoc_logs = conn.execute("SELECT elapsed_hours, tvoc_ppm FROM log_tvoc WHERE batch_id = ? ORDER BY elapsed_hours ASC", (batch_id,)).fetchall()
        telemetry_data["gases_tvoc"] = [{"x": row["elapsed_hours"], "y": row["tvoc_ppm"]} for row in tvoc_logs]

    return telemetry_data
