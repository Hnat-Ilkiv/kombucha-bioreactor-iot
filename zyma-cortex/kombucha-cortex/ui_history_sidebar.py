from datetime import datetime
from typing import Optional

# --- Helper Functions (copied from ui_history.py as they are used by get_history_sidebar_html) ---
def _safe_fmt(value: Optional[float], precision: int = 1, suffix: str = "") -> str:
    """
    A robust helper to format numbers, returning 'Н/Д' on any failure.
    """
    if value is None or not isinstance(value, (int, float)):
        return "Н/Д"
    try:
        return f"{value:.{precision}f}{suffix}"
    except (ValueError, TypeError):
        return "Н/Д"

def _format_datetime(dt_str: Optional[str]) -> str:
    """
    Formats an ISO datetime string for display, or returns 'Н/Д'.
    """
    if not dt_str:
        return "Н/Д"
    try:
        dt_obj = datetime.fromisoformat(dt_str)
        return dt_obj.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return "Н/Д"

# --- Main UI Function for Sidebar History ---
def get_history_sidebar_html(batches: list) -> str:
    """
    Generates a compact sidebar history view as a dense text-styled HTML sub-table.
    """
    rows_html = ""
    if not batches:
        rows_html = """
        <tr>
            <td colspan="3" class="p-1 text-center text-gray-500 text-xs">Немає минулих партій.</td>
        </tr>
        """
    else:
        for batch in batches:
            end_time_string = _format_datetime(batch["end_time"])
            rows_html += f"""
            <tr class="hover:bg-gray-700 cursor-pointer text-xs" hx-get="/api/ui/history/batch/{batch["id"]}/view" hx-target="#node-detail" hx-swap="innerHTML">
              <td class="p-1 font-bold text-blue-400">#{batch["id"]}</td>
              <td class="p-1 font-mono text-gray-300">{batch["device_mac"]}</td>
              <td class="p-1 text-gray-400 text-[10px]">{end_time_string}</td>
            </tr>
            """
    
    return f"""
    <table class="min-w-full">
        <thead>
            <tr>
                <th class="p-1 text-left text-gray-400 text-[10px] uppercase">ID</th>
                <th class="p-1 text-left text-gray-400 text-[10px] uppercase">MAC</th>
                <th class="p-1 text-left text-gray-400 text-[10px] uppercase">Кінець</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """