from datetime import datetime, timezone
from typing import Dict, Any

def get_nodes_table_html(system_state: dict) -> str:
    """
    Returns an HTML partial table component rendering live columns for all nodes.
    Each row triggers an HTMX GET request to load the specific node's dashboard.
    """
    rows_html = ""
    for mac, node_data in sorted(system_state.items()):
        # Determine online status based on the last_seen timestamp
        last_seen = node_data.get("last_seen")
        is_online = False
        last_seen_str = "Ніколи"
        if last_seen:
            # Ensure last_seen is timezone-naive before comparison
            if last_seen.tzinfo:
                last_seen = last_seen.replace(tzinfo=None)
            
            is_online = (datetime.now(timezone.utc).replace(tzinfo=None) - last_seen).total_seconds() < 60
            last_seen_str = last_seen.strftime('%Y-%m-%d %H:%M:%S')

        status_color = "text-green-400" if is_online else "text-red-500"
        
        rows_html += f'''
        <tr class="table-row cursor-pointer" 
            hx-get="/api/ui/node/{mac}/dashboard" 
            hx-target="#node-detail" 
            hx-swap="innerHTML">
            <td class="p-2 font-mono text-sm">{mac}</td>
            <td class="p-2 {status_color}">{ "Онлайн" if is_online else "Офлайн" }</td>
            <td class="p-2 text-xs text-gray-400">{last_seen_str}</td>
        </tr>
        '''

    return f"""
    <table class="w-full text-left">
        <thead class="bg-gray-800 text-xs">
            <tr>
                <th class="p-2">MAC</th>
                <th class="p-2">Статус</th>
                <th class="p-2">Останній контакт</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """
