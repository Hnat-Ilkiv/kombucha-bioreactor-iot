# 1. REQUIREMENTS FOR 'ui_base.py'

# This global string contains the main dark-themed webpage layout.
# It includes CDN links and the primary containers for HTMX swapping.
BASE_HTML = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <title>Zyma Cortex - IIoT Dashboard</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #111827; color: #e5e7eb; }
        .sidebar { border-right: 1px solid #374151; }
        .form-input { background-color: #374151; border: 1px solid #4b5563; color: white; }
        .table-row:hover { background-color: #374151; }
    </style>
</head>
<body class="flex h-screen">
    <!-- Left sidebar for node listing and history -->
    <div class="sidebar w-1/3 max-w-xs p-4 flex flex-col h-screen overflow-hidden space-y-4 border-r border-gray-700">
        <!-- Top Half: Active Nodes -->
        <div class="flex-1 overflow-y-auto min-h-[45%] border-b border-gray-700 pb-4">
            <h2 class="text-lg font-bold mb-2 text-gray-200">Системні ноди</h2>
            <div id="nodes-sidebar" hx-get="/api/ui/nodes_table" hx-trigger="load, every 5s" hx-swap="innerHTML">
                <!-- Node table partial is loaded here -->
            </div>
        </div>
        <!-- Bottom Half: Batch History -->
        <div class="flex-1 overflow-y-auto min-h-[45%] pt-2">
            <h2 class="text-lg font-bold mb-2 text-gray-200">Архів партій</h2>
            <div id="history-sidebar" hx-get="/api/ui/history_sidebar" hx-trigger="load, every 10s" hx-swap="innerHTML">
                <!-- History partial is loaded here -->
            </div>
        </div>
    </div>
    <!-- Right container for node-specific details -->
    <div id="node-detail" class="flex-1 p-6 overflow-y-auto">
        <div class="text-gray-500">Оберіть ноду для перегляду деталей...</div>
    </div>
</body>
</html>
"""
