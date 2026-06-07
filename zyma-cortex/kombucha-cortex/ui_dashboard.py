from typing import Dict, Any

# 2. INTEGRITY ENFORCEMENT: Maintain absolute flat imports
from ui_telemetry import get_node_stats_html
from ui_controls import get_control_panel_html
from ui_charts import get_node_charts_html

def get_node_dashboard_html(mac: str, node_data: Dict[str, Any]) -> str:
    """
    Main destructuring hook. This function acts as a layout organizer,
    combining all atomized UI components into a unified dashboard layout.
    """
    batch_data = node_data.get("batch", {})

    # Retrieve HTML fragments from dedicated component modules
    stats_html = get_node_stats_html(mac, node_data)
    controls_html = get_control_panel_html(mac, batch_data)
    charts_html = get_node_charts_html(mac)

    # 1. LINEAR STACK ARCHITECTURE: Build a clean single-column vertical layout
    return f"""
    <div class="space-y-6">
        <h3 class="text-2xl font-bold">Дешборд: {mac}</h3>
        
        <div class="flex flex-col space-y-6 w-full">
            <!-- Block 1 (Top, 100% width): Live metrics box container -->
            <div id="live-metrics-box" class="w-full" hx-get="/api/ui/node/{mac}/stats" hx-trigger="load, every 5s" hx-swap="innerHTML">
                {stats_html}
            </div>
            
            <!-- Block 2 (Middle, 100% width): Hardware execution control panel -->
            <div class="w-full">
                {controls_html}
            </div>
            
            <!-- Block 3 (Bottom, 100% width): Chart engine container -->
            <div class="w-full">
                {charts_html}
            </div>
        </div>
    </div>
    """
