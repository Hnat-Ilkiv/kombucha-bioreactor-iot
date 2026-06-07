def get_node_charts_html(mac: str) -> str:
    """
    Returns an HTML fragment with three Chart.js canvas containers and the
    self-contained JavaScript for polling data and rendering all three charts
    with corrected escaping, explicit axis scaling, and a safe re-use lifecycle.
    """
    return f"""
    <div class="grid grid-cols-1 gap-6 w-full" id="charts-grid-container">
        <div class="bg-gray-800 p-4 rounded-lg">
            <h4 class="font-semibold mb-2">Термодинаміка (°C)</h4>
            <div class="w-full h-[500px] max-h-[500px]"><canvas id="tempChart"></canvas></div>
        </div>
        <div class="bg-gray-800 p-4 rounded-lg">
            <h4 class="font-semibold mb-2">Біокінетика (pH)</h4>
            <div class="w-full h-[500px] max-h-[500px]"><canvas id="phChart"></canvas></div>
        </div>
        <div class="bg-gray-800 p-4 rounded-lg">
            <h4 class="font-semibold mb-2">Аналіз газів (ppm)</h4>
            <div class="w-full h-[500px] max-h-[500px]"><canvas id="gasChart"></canvas></div>
        </div>
    </div>

    <script>
      (function() {{
        const mac = "{mac}";
        
        // ISOLATED MAC-BASED INSTANCE CACHING MAP
        window.zymaCharts = window.zymaCharts || {{}};
        // Dynamically bind to the unique MAC address string
        window.zymaCharts["' + mac + '"] = window.zymaCharts["' + mac + '"] || {{}};
        const nodeCache = window.zymaCharts["' + mac + '"]; // Local reference for current node's charts

        const updateOrCreateChart = (id, config) => {{
            const ctx = document.getElementById(id)?.getContext('2d');
            if (!ctx) return;

            let chart = nodeCache[id]; // Access from node-specific cache
            if (chart && document.body.contains(chart.ctx.canvas)) {{
                chart.data.datasets.forEach((dataset, i) => {{
                    dataset.data = config.data.datasets[i].data;
                }});
                // Update scale max based on new data
                if (config.options.scales.x.max) {{
                    chart.options.scales.x.max = config.options.scales.x.max;
                }}
                chart.update("none");
            }} else {{
                if (chart) {{ chart.destroy(); }} // Destroy if exists but not in DOM
                config.options.responsive = true;
                config.options.maintainAspectRatio = false;
                nodeCache[id] = new Chart(ctx, config); // Save to node-specific cache
            }}
        }};

        const fetchAndRenderCharts = async () => {{
            try {{
                const response = await fetch("/api/ui/node/" + mac.replace("$", "").replace("%24", "") + "/chart_data");
                if (!response.ok) return;
                const data = await response.json();
                
                const xAxisMax = Math.ceil(data.t_max * 1.01);

                updateOrCreateChart('tempChart', {{
                    type: 'line',
                    data: {{
                        datasets: [
                            {{ label: 'Рідина', data: data.temps_liquid, borderColor: '#f87171' }},
                            {{ label: 'Нагрівач', data: data.temps_bed, borderColor: '#fb923c' }},
                            {{ label: 'Поверхня', data: data.temps_surface, borderColor: '#4ade80' }}
                        ]
                    }},
                    options: {{
                        scales: {{
                            x: {{ type: "linear", min: 0, max: xAxisMax, title: {{ display: true, text: "Час процесу (год)" }}, ticks: {{ stepSize: 12 }} }}
                        }},
                        y: {{ beginAtZero: false, ticks: {{ precision: 1 }} }}
                    }}
                }});

                updateOrCreateChart('phChart', {{
                    type: 'line',
                    data: {{
                        datasets: [
                            {{ label: 'Розрахунковий pH', data: data.phs, borderColor: '#60a5fa' }}
                        ]
                    }},
                    options: {{
                        scales: {{
                            x: {{ type: "linear", min: 0, max: xAxisMax, title: {{ display: true, text: "Час процесу (год)" }}, ticks: {{ stepSize: 12 }} }},
                            y: {{ min: 2.5, max: 5.5, ticks: {{ stepSize: 0.5 }} }}
                        }}
                    }}
                }});

                updateOrCreateChart('gasChart', {{
                    type: 'line',
                    data: {{
                        datasets: [
                            {{ label: 'Етанол (ppm)', data: data.gases_ethanol, borderColor: '#a78bfa' }},
                            {{ label: 'TVOC (ppm)', data: data.gases_tvoc_ppm, borderColor: '#d8b4fe' }}
                        ]
                    }},
                    options: {{
                        scales: {{
                            x: {{ type: "linear", min: 0, max: xAxisMax, title: {{ display: true, text: "Час процесу (год)" }}, ticks: {{ stepSize: 12 }} }}
                        }},
                        y: {{ beginAtZero: true }}
                    }}
                }});

            }} catch (e) {{ console.error("Chart update failed:", e); }}
        }};
        
        const intervalId = setInterval(fetchAndRenderCharts, 5000);
        fetchAndRenderCharts();

        // FIX HTMX SWAP UNMOUNT CLEANUP LOOP
        const chartCleanupHandler = (event) => {{
            if (event.detail.target && event.detail.target.id === "node-detail") {{
                clearInterval(intervalId);
                Object.values(nodeCache).forEach(c => {{ if(c && c.destroy) c.destroy(); }});
                window.zymaCharts["' + mac + '"] = {{}}; // Clear this node's cache
                document.removeEventListener("htmx:beforeSwap", chartCleanupHandler);
            }}
        }};
        document.addEventListener("htmx:beforeSwap", chartCleanupHandler);
      }})();
    </script>
    """