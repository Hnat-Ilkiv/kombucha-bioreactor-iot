def get_historical_charts_script(batch_id: int) -> str:
    """
    Returns the JavaScript rendering script for Chart.js historical data.
    Uses placeholders for dynamic data replacement downstream.
    """
    js_template = """
        <script>
          (function() {
            const batchId = "__BATCH_ID__";
            // Use a separate cache for historical charts to avoid conflict with live charts
            window.zymaHistoricalCharts = window.zymaHistoricalCharts || {};

            const updateOrCreateHistoricalChart = (id, config) => {
                const ctx = document.getElementById(id)?.getContext('2d');
                if (!ctx) return;

                let chart = window.zymaHistoricalCharts[id];
                if (chart) {
                    chart.data.datasets.forEach((dataset, i) => {
                        dataset.data = config.data.datasets[i].data;
                    });
                    if (config.options.scales.x.max) {
                        chart.options.scales.x.max = config.options.scales.x.max;
                    }
                    chart.update("none");
                } else {
                    if (chart) { chart.destroy(); }
                    config.options.responsive = true;
                    config.options.maintainAspectRatio = false;
                    window.zymaHistoricalCharts[id] = new Chart(ctx, config);
                }
            };

            const fetchAndRenderHistoricalCharts = async () => {
                try {
                    const response = await fetch("/api/ui/history/batch/" + batchId + "/chart_data");
                    if (!response.ok) return;
                    const data = await response.json();
                    
                    const xAxisMax = data.t_max;

                    updateOrCreateHistoricalChart('tempHistoricalChart', {
                        type: 'line',
                        data: {
                            datasets: [
                                { label: 'Рідина', data: data.temps_liquid, borderColor: '#f87171' },
                                { label: 'Нагрівач', data: data.temps_bed, borderColor: '#fb923c' },
                                { label: 'Поверхня', data: data.temps_surface, borderColor: '#4ade80' },
                                { label: 'Цільова', data: data.temp_target, borderColor: '#818cf8', borderDash: [5, 5] }
                            ]
                        },
                        options: {
                            scales: {
                                x: { type: "linear", min: 0, max: xAxisMax, title: { display: true, text: "Час процесу (год)" }, ticks: { stepSize: 12 } }
                            },
                            y: { beginAtZero: false, ticks: { precision: 1 } }
                        }
                    });

                    updateOrCreateHistoricalChart('phHistoricalChart', {
                        type: 'line',
                        data: {
                            datasets: [
                                { label: 'Розрахунковий pH', data: data.phs, borderColor: '#60a5fa' }
                            ]
                        },
                        options: {
                            scales: {
                                x: { type: "linear", min: 0, max: xAxisMax, title: { display: true, text: "Час процесу (год)" }, ticks: { stepSize: 12 } }
                            },
                            y: { min: 2.5, max: 5.5, ticks: { stepSize: 0.5 } }
                        }
                    });

                    updateOrCreateHistoricalChart('gasHistoricalChart', {
                        type: 'line',
                        data: {
                            datasets: [
                                { label: 'Етанол (ppm)', data: data.gases_ethanol, borderColor: '#a78bfa' },
                                { label: 'TVOC (ppm)', data: data.gases_tvoc_ppm, borderColor: '#d8b4fe' }
                            ]
                        },
                        options: {
                            scales: {
                                x: { type: "linear", min: 0, max: xAxisMax, title: { display: true, text: "Час процесу (год)" }, ticks: { stepSize: 12 } }
                            },
                            y: { beginAtZero: true }
                        }
                    });

                } catch (e) { console.error("Historical chart update failed:", e); }
            };
            
            fetchAndRenderHistoricalCharts(); // Load data ONCE

            // Cleanup when HTMX swaps this component out
            const historicalChartsCleanup = (event) => {
                if (event.detail.target && event.detail.target.id === "node-detail") {
                    Object.values(window.zymaHistoricalCharts).forEach(chart => { if(chart && chart.destroy) chart.destroy(); });
                    window.zymaHistoricalCharts = {};
                    document.removeEventListener("htmx:beforeSwap", historicalChartsCleanup);
                }
            };
            document.addEventListener("htmx:beforeSwap", historicalChartsCleanup);
          })();
        </script>
    """
    return js_template.replace("__BATCH_ID__", str(batch_id))