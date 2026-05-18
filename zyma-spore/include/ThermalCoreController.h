#ifndef THERMAL_CORE_CONTROLLER_H
#define THERMAL_CORE_CONTROLLER_H

#include <Arduino.h>
#include "PowerHeaterDriver.h"
#include "NetworkMqttManager.h"

/**
 * @class ThermalCoreController
 * @brief Інкапсулює всю математичну логіку та керування станом для термального ядра біореактора.
 * 
 * Цей клас відповідає за:
 * 1. Фільтрацію вхідних даних з датчиків.
 * 2. Аварійний арбітраж та логування помилок.
 * 3. Розрахунок керуючої потужності нагрівача на основі нелінійної моделі.
 * 4. Збереження відфільтрованого стану температур для телеметрії.
 */
class ThermalCoreController {
public:
  ThermalCoreController();

  /**
   * @brief Ініціалізує ядро, передаючи посилання на необхідні драйвери.
   * @param heater Посилання на об'єкт драйвера силового ключа нагрівача.
   * @param net Посилання на об'єкт менеджера мережі для відправки логів.
   */
  void begin(PowerHeaterDriver& heater, NetworkMqttManager& net);

  /**
   * @brief Основний цикл оновлення стану та розрахунку. Викликається на кожній ітерації головного циклу.
   * @param now Поточний час в мілісекундах (від millis()).
   * @param target Цільова температура для рідини.
   * @param processEnabled Поточний стан процесу (true = RUN, false = STOP).
   * @param rawBed "Сира" температура з датчика нагрівального столу.
   * @param rawSurface "Сира" температура з датчика поверхні культури.
   * @param rawLiquid "Сира" температура з датчика рідини.
   */
  void update(unsigned long now, float target, bool processEnabled, float rawBed, float rawSurface, float rawLiquid);

  // --- Методи доступу до відфільтрованих даних ---
  float getFilteredBed() const;
  float getFilteredSurface() const;
  float getFilteredLiquid() const;

private:
  // --- Зовнішні залежності ---
  PowerHeaterDriver* _heater = nullptr;
  NetworkMqttManager* _net = nullptr;
  
  // --- Аварійні пороги безпеки та константи моделі ---
  static constexpr float MAX_SAFE_BED_TEMP = 65.0f;
  static constexpr float MAX_SAFE_SURFACE_TEMP = 55.0f;
  static constexpr float MAX_SAFE_LIQUID_TEMP = 40.0f;
  static constexpr float MAX_PRODUCTION_POWER = 100.0f;

  // --- Внутрішній стан контролера ---
  float _filteredBed = -999.0f;
  float _filteredSurface = -999.0f;
  float _filteredLiquid = -999.0f;

  // --- Прапорці для обмеження частоти логування помилок (Throttling) ---
  bool _faultLogged_bedDisconnect = false;
  bool _faultLogged_bedOverheat = false;
  bool _faultLogged_surfaceDisconnect = false;
  bool _faultLogged_surfaceOverheat = false;
  bool _faultLogged_liquidDisconnect = false;
  bool _faultLogged_liquidOverheat = false;
};

#endif // THERMAL_CORE_CONTROLLER_H
