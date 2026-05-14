#include <Arduino.h>
#include <Preferences.h>
#include "secrets.h"
#include "RemoteUpdateManager.h"
#include "ThermistorNTC.h"
#include "OneWireTemperatureManager.h"
#include "PowerHeaterDriver.h"
#include "AmbientEnvManager.h"
#include "NetworkMqttManager.h"
#include "ThermalCoreController.h"
#include "BioGasManager.h"
#include "GasAnalogAnalyzer.h"

// ================= ІНІЦІАЛІЗАЦІЯ ОБ'ЄКТІВ-МЕНЕДЖЕРІВ =================
Preferences preferences;
NetworkMqttManager netManager;
RemoteUpdateManager remoteUpdateManager;
ThermalCoreController thermalCore;
BioGasManager bioGasManager;
GasAnalogAnalyzer gasAnalogAnalyzer;

// ================= ІНІЦІАЛІЗАЦІЯ ОБ'ЄКТІВ-ДРАЙВЕРІВ =================
ThermistorNTC bedThermistor(34, 3950.0f, 100000.0f, 100000.0f, 4.18f);
OneWireTemperatureManager owTempManager(4);
PowerHeaterDriver heaterDriver(26);
AmbientEnvManager ambientEnvManager;

// ================= ГЛОБАЛЬНІ УСТАВКИ ТА СТАН =================
float targetTemperature = 24.0f;
bool processEnabled = false;
unsigned long lastControlCycle = 0;
unsigned long lastTelemetryCycle = 0;
constexpr unsigned long CONTROL_INTERVAL = 1000;
constexpr unsigned long TELEMETRY_INTERVAL = 5000;

/**
 * @brief Головна функція ініціалізації (виконується один раз).
 * 
 * Оркеструє запуск всіх модулів: мережа, драйвери, математичне ядро.
 */
void setup() {
  Wire.begin(21, 22);
  Wire.setClock(20000); // Фіксація швидкості для сумісності з AGS02MA

  heaterDriver.begin();

  preferences.begin("kombucha", false);
  targetTemperature = preferences.getFloat("target_t", 24.0f);
  processEnabled = preferences.getBool("process_en", false);
  
  netManager.begin(WIFI_SSID, WIFI_PASSWORD, "192.168.0.201", 1883, 
      [](float newTarget) {
          targetTemperature = newTarget;
          preferences.putFloat("target_t", targetTemperature);
      },
      [](bool newRunState) {
          processEnabled = newRunState;
          preferences.putBool("process_en", processEnabled);
      }
  );
  
  // Створення функціонального об'єкта (лямбди) для перенаправлення логів у MQTT
  auto forwarder = [](String message) { netManager.logDebug(message); };

  bedThermistor.begin();
  owTempManager.begin(forwarder);
  ambientEnvManager.begin(Wire, forwarder);
  bioGasManager.begin(Wire, forwarder);
  gasAnalogAnalyzer.begin(35, forwarder);
  remoteUpdateManager.begin("zyma-spore-node", heaterDriver, forwarder);
  
  // Ініціалізація математичного ядра з посиланнями на драйвери
  thermalCore.begin(heaterDriver, netManager);
  
  netManager.logDebug("System Initialized. Target: " + String(targetTemperature, 2) + 
                       "C. Process: " + String(processEnabled ? "RUN" : "STOP") + 
                       ". IP: " + WiFi.localIP().toString());
  
  owTempManager.requestTemperatures(); // Перший запит для заповнення даних
}

/**
 * @brief Головний цикл програми (виконується нескінченно).
 * 
 * Виступає в ролі чистого декларативного оркестратора:
 * 1. Обслуговує асинхронні обробники (OTA, MQTT, Нагрівач, Сенсори).
 * 2. Зчитує сирі дані та передає їх у математичне ядро для обробки (1 раз/сек).
 * 3. Публікує відфільтровану телеметрію (1 раз/5 сек).
 */
void loop() {
  unsigned long now = millis();

  // --- Асинхронні обробники ---
  netManager.handle(now, []() {
    heaterDriver.setPowerPercent(0);
    heaterDriver.handle();
  });
  remoteUpdateManager.handle();
  heaterDriver.handle();
  ambientEnvManager.handle();
  bioGasManager.handle(now);
  gasAnalogAnalyzer.handle(now);

  // --- ШВИДКИЙ КОНТУР КЕРУВАННЯ (1000ms) ---
  if (now - lastControlCycle >= CONTROL_INTERVAL) {
    lastControlCycle = now;
    
    // Делегування всієї логіки в ядро
    thermalCore.update(now, targetTemperature, processEnabled,
                       bedThermistor.readTemperatureCelsius(),
                       owTempManager.getSurfaceTemperature(),
                       owTempManager.getLiquidTemperature());
                       
    owTempManager.requestTemperatures(); // Запит на наступну ітерацію
  }

  // --- ПОВІЛЬНИЙ КОНТУР ТЕЛЕМЕТРІЇ (5000ms) ---
  if (now - lastTelemetryCycle >= TELEMETRY_INTERVAL) {
    lastTelemetryCycle = now;

    float bed = thermalCore.getFilteredBed();
    if (bed != -999.0f) netManager.publishTelemetry(netManager.SUFFIX_TEMP_BED, bed);

    float surf = thermalCore.getFilteredSurface();
    if (surf != -999.0f) netManager.publishTelemetry(netManager.SUFFIX_TEMP_SURFACE, surf);

    float liq = thermalCore.getFilteredLiquid();
    if (liq != -999.0f) netManager.publishTelemetry(netManager.SUFFIX_TEMP_LIQUID, liq);

    float ambT = ambientEnvManager.getAmbientTemperature();
    if (ambT != -999.0f) netManager.publishTelemetry(netManager.SUFFIX_TEMP_AMBIENT, ambT);

    float ambH = ambientEnvManager.getAmbientHumidity();
    if (ambH != -999.0f) netManager.publishTelemetry(netManager.SUFFIX_HUMID_AMBIENT, ambH);

    float tvoc = bioGasManager.getAgsTvoc();
    if (tvoc != -1.0f) netManager.publishTelemetry(netManager.SUFFIX_GAS_DIGITAL, tvoc);

    float ethPpm = gasAnalogAnalyzer.getEthanolPpm();
    if (ethPpm != -1.0f) netManager.publishTelemetry(netManager.SUFFIX_GAS_ANALOG, ethPpm);

    netManager.publishTelemetry(netManager.SUFFIX_PROCESS_STATE, processEnabled ? 1.0f : 0.0f);
    netManager.publishTelemetry(netManager.SUFFIX_HEATER_POWER, (float)heaterDriver.getPowerPercent());

    netManager.logDebug("Control | Heater Power: " + String(heaterDriver.getPowerPercent()) + "%");
  }
}
