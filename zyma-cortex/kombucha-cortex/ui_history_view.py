from datetime import datetime
from typing import Optional

from ui_history_charts import get_historical_charts_script

# --- Helper Functions (Copied from ui_history.py) ---
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

# --- Main UI Functions ---
def get_history_page_html(batches_list: list) -> str:
    """
    Generates the HTML for the historical batches list page.
    """
    rows_html = ""
    for batch in batches_list:
        start_time_fmt = _format_datetime(batch["start_time"])
        end_time_fmt = _format_datetime(batch["end_time"]) if batch["end_time"] else "В процесі"
        
        rows_html += f"""
        <tr class="hover:bg-gray-700 hx-get="/api/ui/history/batch/{str(batch["id"])}/view" hx-target="#node-detail" hx-swap="innerHTML">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-100">{batch["id"]}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{batch["device_mac"]}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{start_time_fmt}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{end_time_fmt}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{_safe_fmt(batch["volume_ml"], 0)} мл</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{_safe_fmt(batch["sugar_g"], 0)} г</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{_safe_fmt(batch["culture_mass_g"], 0)} г</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{_safe_fmt(batch["ph_start"], 1)}</td>
        </tr>
        """

    return f"""
    <div class="p-4 bg-gray-900 text-white min-h-screen">
        <h2 class="text-2xl font-bold mb-4 text-gray-100">Історія Партій</h2>
        <div class="overflow-x-auto bg-gray-800 rounded-lg shadow">
            <table class="min-w-full divide-y divide-gray-700">
                <thead class="bg-gray-700">
                    <tr>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-200 uppercase tracking-wider">ID</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-200 uppercase tracking-wider">MAC Ноди</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-200 uppercase tracking-wider">Старт</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-200 uppercase tracking-wider">Кінець</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-200 uppercase tracking-wider">Об'єм</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-200 uppercase tracking-wider">Цукор</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-200 uppercase tracking-wider">Культура</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-200 uppercase tracking-wider">pH Старт</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-800">
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    """

def get_historical_dashboard_html(batch_row: dict) -> str:
    """
    Renders a static dashboard mirroring the live view but with static batch metadata
    and non-polling Chart.js coordinate canvasses for a historical batch.
    """
    # Static metadata cards - this can remain an f-string
    metadata_cards_html = f"""
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <div class="bg-gray-800 p-4 rounded-lg shadow-md">
            <div class="text-sm text-gray-400">ID Партії</div>
            <div class="text-xl font-bold text-gray-100">{batch_row['id']}</div>
        </div>
        <div class="bg-gray-800 p-4 rounded-lg shadow-md">
            <div class="text-sm text-gray-400">MAC Ноди</div>
            <div class="text-xl font-bold text-gray-100">{batch_row['device_mac']}</div>
        </div>
        <div class="bg-gray-800 p-4 rounded-lg shadow-md">
            <div class="text-sm text-gray-400">Запуск</div>
            <div class="text-xs font-bold text-gray-100">{_format_datetime(batch_row['start_time'])}</div>
        </div>
        <div class="bg-gray-800 p-4 rounded-lg shadow-md">
            <div class="text-sm text-gray-400">Завершення</div>
            <div class="text-xs font-bold text-gray-100">{_format_datetime(batch_row['end_time'])}</div>
        </div>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-gray-800 p-4 rounded-lg shadow-md">
            <div class="text-sm text-gray-400">Об'єм чайного субстрату</div>
            <div class="text-xl font-bold text-gray-100">{_safe_fmt(batch_row['volume_ml'], 0)} мл</div>
        </div>
        <div class="bg-gray-800 p-4 rounded-lg shadow-md">
            <div class="text-sm text-gray-400">Маса цукру</div>
            <div class="text-xl font-bold text-gray-100">{_safe_fmt(batch_row['sugar_g'], 0)} г</div>
        </div>
        <div class="bg-gray-800 p-4 rounded-lg shadow-md">
            <div class="text-sm text-gray-400">Маса SCOBY</div>
            <div class="text-xl font-bold text-gray-100">{_safe_fmt(batch_row['culture_mass_g'], 0)} г</div>
        </div>
        <div class="bg-gray-800 p-4 rounded-lg shadow-md">
            <div class="text-sm text-gray-400">Початковий pH</div>
            <div class="text-xl font-bold text-gray-100">{_safe_fmt(batch_row['ph_start'], 1)}</div>
        </div>
    </div>
    """

    layout_template = """
    <div class="p-4 bg-gray-900 text-white min-h-screen">
        <h2 class="text-2xl font-bold mb-6 text-gray-100">Історична партія (ID: __BATCH_ID__)</h2>
        <button hx-get="/api/ui/history" hx-target="#node-detail" hx-swap="innerHTML" class="mb-6 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded">
            &larr; Назад до списку партій
        </button>

        __METADATA_CARDS_HTML__

        <div class="grid grid-cols-1 gap-6 w-full mt-6" id="charts-grid-container">
            <div class="bg-gray-800 p-4 rounded-lg">
                <h4 class="font-semibold mb-2">Термодинаміка (°C)</h4>
                <div class="w-full h-[500px] max-h-[500px]"><canvas id="tempHistoricalChart"></canvas></div>
            </div>
            <div class="bg-gray-800 p-4 rounded-lg">
                <h4 class="font-semibold mb-2">Біокінетика (pH)</h4>
                <div class="w-full h-[500px] max-h-[500px]"><canvas id="phHistoricalChart"></canvas></div>
            </div>
            <div class="bg-gray-800 p-4 rounded-lg">
                <h4 class="font-semibold mb-2">Аналіз газів (ppm)</h4>
                <div class="w-full h-[500px] max-h-[500px]"><canvas id="gasHistoricalChart"></canvas></div>
            </div>
        </div>

        __CHARTS_SCRIPT__
    </div>
    """
    return layout_template.replace("__BATCH_ID__", str(batch_row["id"])).replace("__DEVICE_MAC__", str(batch_row["device_mac"])).replace("__METADATA_CARDS_HTML__", metadata_cards_html).replace("__CHARTS_SCRIPT__", get_historical_charts_script(batch_row["id"]))