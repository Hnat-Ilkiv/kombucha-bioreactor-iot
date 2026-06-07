from typing import Dict, Any, Optional

def safe_fmt(data: dict, key: str, precision: int = 1, suffix: str = "") -> str:
    """
    A robust helper to format dictionary values, returning 'Н/Д' on any failure.
    Protects the UI from crashing if a key is missing or data is malformed.
    """
    val = data.get(key)
    if val is None or not isinstance(val, (int, float)):
        return "Н/Д"
    try:
        # Use a dynamic f-string to handle precision
        return f"{{val:.{precision}f}}{{suffix}}".format(val=val, suffix=suffix)
    except (ValueError, TypeError):
        return "Н/Д"

def get_node_stats_html(mac: str, node_data: Dict[str, Any]) -> str:
    """
    Builds a responsive, comprehensive industrial telemetry grid rendering 12 distinct
    parameters, grouped into 5 logical sections.
    """
    metrics = node_data.get("metrics", {})
    batch = node_data.get("batch", {})
    
    process_state_text = "АКТИВНИЙ НАГРІВ" if metrics.get('process_state') == 1.0 else "ОЧІКУВАННЯ"
    
    return f"""
    <div class="space-y-6">
        <!-- Section 1: Thermodynamics -->
        <div>
            <h4 class="font-semibold text-gray-400 mb-2">Термодинаміка</h4>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div class="bg-gray-700 p-3 rounded-lg">
                    <div class="text-xs text-gray-400">Рідина</div>
                    <div class="text-xl font-bold">{safe_fmt(metrics, 'liquid_temp_c', suffix='°C')}</div>
                </div>
                <div class="bg-gray-700 p-3 rounded-lg">
                    <div class="text-xs text-gray-400">Поверхня</div>
                    <div class="text-xl font-bold">{safe_fmt(metrics, 'surface_temp_c', suffix='°C')}</div>
                </div>
                <div class="bg-gray-700 p-3 rounded-lg">
                    <div class="text-xs text-gray-400">Нагрівач</div>
                    <div class="text-xl font-bold">{safe_fmt(metrics, 'bed_temp_c', suffix='°C')}</div>
                </div>
                <div class="bg-blue-800 p-3 rounded-lg">
                    <div class="text-xs text-blue-300">Цільова t°</div>
                    <div class="text-xl font-bold">{safe_fmt(batch, 'target_temp', suffix='°C')}</div>
                </div>
            </div>
        </div>

        <!-- Section 2: Biokinetics & Gases -->
        <div>
            <h4 class="font-semibold text-gray-400 mb-2">Біокінетика та Гази</h4>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div class="bg-blue-800 p-3 rounded-lg">
                    <div class="text-xs text-blue-300">Розрахунковий pH</div>
                    <div class="text-xl font-bold">{safe_fmt(batch, 'predicted_ph', precision=3)}</div>
                </div>
                <div class="bg-gray-700 p-3 rounded-lg">
                    <div class="text-xs text-gray-400">TVOC</div>
                    <div class="text-xl font-bold">{safe_fmt(metrics, 'digital_tvoc_ppm', precision=3, suffix=' ppm')}</div>
                </div>
                <div class="bg-gray-700 p-3 rounded-lg">
                    <div class="text-xs text-gray-400">Етанол</div>
                    <div class="text-xl font-bold">{safe_fmt(metrics, 'analog_ethanol_ppm', suffix=' ppm')}</div>
                </div>
            </div>
        </div>

        <!-- Sections 3 & 4: Environment & Time Bounds -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <h4 class="font-semibold text-gray-400 mb-2">Середовище</h4>
                <div class="grid grid-cols-2 gap-4 text-center">
                    <div class="bg-gray-700 p-3 rounded-lg">
                        <div class="text-xs text-gray-400">Температура</div>
                        <div class="text-xl font-bold">{safe_fmt(metrics, 'ambient_temp_c', suffix='°C')}</div>
                    </div>
                    <div class="bg-gray-700 p-3 rounded-lg">
                        <div class="text-xs text-gray-400">Вологість</div>
                        <div class="text-xl font-bold">{safe_fmt(metrics, 'ambient_humid_pct', suffix='%')}</div>
                    </div>
                </div>
            </div>
            <div>
                <h4 class="font-semibold text-gray-400 mb-2">Часові рамки</h4>
                <div class="grid grid-cols-3 gap-4 text-center">
                    <div class="bg-gray-700 p-3 rounded-lg">
                        <div class="text-xs text-gray-400">t° min</div>
                        <div class="text-xl font-bold">{safe_fmt(batch, 't_min_hours', suffix=' год')}</div>
                    </div>
                    <div class="bg-blue-800 p-3 rounded-lg">
                        <div class="text-xs text-blue-300">Дедлайн</div>
                        <div class="text-xl font-bold">{safe_fmt(batch, 't_desired_hours', suffix=' год')}</div>
                    </div>
                    <div class="bg-gray-700 p-3 rounded-lg">
                        <div class="text-xs text-gray-400">t° max</div>
                        <div class="text-xl font-bold">{safe_fmt(batch, 't_max_hours', suffix=' год')}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Section 5: Actuators -->
        <div>
            <h4 class="font-semibold text-gray-400 mb-2">Виконавчі механізми</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-center">
                <div class="bg-gray-700 p-3 rounded-lg">
                    <div class="text-xs text-gray-400">Потужність ШІМ</div>
                    <div class="text-xl font-bold">{safe_fmt(metrics, 'heater_power_pct', precision=0, suffix='%')}</div>
                </div>
                <div class="bg-gray-700 p-3 rounded-lg">
                    <div class="text-xs text-gray-400">Стан Mosfet</div>
                    <div class="text-xl font-bold">{process_state_text}</div>
                </div>
            </div>
        </div>
    </div>
    """

