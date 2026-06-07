from typing import Dict

def get_control_panel_html(mac: str, batch_data: dict) -> str:
    """
    Renders the appropriate control panel based on the batch active state.
    Separates start, stop, and calibration forms into distinct POST routes.
    """
    return_html = f"""
    <style>
        /* Enforce input text readability on dark backgrounds */
        input.form-input {{ background-color: #1f2937 !important; color: #ffffff !important; }}
    </style>
    """

    if batch_data.get("active", False):
        # Render the active batch view with stop and calibration controls
        t_min = batch_data.get("t_min_hours", 24.0)
        t_max = batch_data.get("t_max_hours", 120.0)
        t_curr = batch_data.get("t_desired_hours", 72.0)

        return_html += f"""
        <div class="bg-gray-800 p-4 rounded-lg">
            <h4 class="text-lg font-semibold mb-3">Активна партія (ID: {batch_data.get('id', 'N/A')})</h4>
            <div class="flex flex-col gap-4">
                <!-- Stop Form -->
                <form hx-post="/api/control/{mac}/stop" hx-target="#node-detail" hx-swap="innerHTML">
                    <button type="submit" class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded">
                        Примусово зупинити
                    </button>
                </form>
                <!-- Calibration Form -->
                <form hx-post="/api/control/{mac}/calibrate" hx-target="#node-detail" hx-swap="innerHTML" class="flex flex-col gap-2 bg-gray-900 p-2 rounded border border-gray-700">
                    <div class="flex items-center gap-2 bg-gray-900 border border-gray-700 p-2 rounded text-sm text-gray-200">
                        <label class="flex-1 text-center py-2 px-4 rounded text-xs font-bold cursor-pointer transition-all bg-gray-800 border border-gray-600 has-[:checked]:bg-blue-600 has-[:checked]:text-white">
                            <input type="radio" name="precision_level" value="digital" class="hidden" checked>Цифровий рН
                        </label>
                        <label class="flex-1 text-center py-2 px-4 rounded text-xs font-bold cursor-pointer transition-all bg-gray-800 border border-gray-600 has-[:checked]:bg-blue-600 has-[:checked]:text-white">
                            <input type="radio" name="precision_level" value="strips" class="hidden">Смужки
                        </label>
                    </div>
                    <input type="number" step="0.01" min="2.0" max="7.0" name="manual_ph" placeholder="Виміряний pH" class="form-input flex-grow p-2 rounded" required>
                    <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
                        Калібрувати
                    </button>
                </form>
                <!-- Deadline Slider -->
                <form hx-post="/api/control/{mac}/adjust_deadline" hx-trigger="change" hx-target="#node-detail" hx-swap="innerHTML" class="bg-gray-700 p-3 rounded-lg mt-2">
                    <label class="text-xs text-gray-400 block mb-1">Корекція дедлайну системи (MPC)</label>
                    <input type="range" name="t_desired_hours" min="0" max="{t_max}" step="1" value="{t_curr}" class="w-full" oninput="this.nextElementSibling.value = this.value + ' год'">
                    <output class="text-sm font-bold text-blue-400">{t_curr} год</output>
                    <div class="text-xs text-orange-400 mt-1">Мінімальний час форсажу (t_min): {t_min} год</div>
                </form>
            </div>
        </div>
        """
    else:
        # Render the start form for a new batch
        return_html += f"""
        <div class="bg-gray-800 p-4 rounded-lg">
            <h4 class="text-lg font-semibold mb-3">Запустити нову партію</h4>
            <form hx-post="/api/control/{mac}/start" hx-target="#node-detail" hx-swap="innerHTML" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input type="number" step="0.1" name="ph_start" placeholder="Початковий pH" value="5.0" class="form-input p-2 rounded" required>
                    <input type="number" name="volume_ml" placeholder="Об'єм (мл)" value="4000" class="form-input p-2 rounded">
                    <input type="number" name="sugar_g" placeholder="Цукор (г)" value="300" class="form-input p-2 rounded">
                    <input type="number" step="0.1" name="culture_mass_g" placeholder="Маса культури (г)" value="200" class="form-input p-2 rounded">
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                    Запустити
                </button>
            </form>
        </div>
        """
    return return_html
