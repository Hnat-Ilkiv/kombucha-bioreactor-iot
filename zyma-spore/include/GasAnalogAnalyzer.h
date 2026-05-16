#ifndef GAS_ANALOG_ANALYZER_H
#define GAS_ANALOG_ANALYZER_H

#include <Arduino.h>
#include <functional>

/**
 * @class GasAnalogAnalyzer
 * @brief Асинхронний менеджер для роботи з аналоговим газовим сенсором MiCS-5524.
 * 
 * Клас інкапсулює логіку опитування аналогового порту з оверсемплінгом,
 * автоматичною калібрацією базового опору (R0) та розрахунком
 * приблизної концентрації етанолу в ppm за допомогою степеневої апроксимації.
 */
class GasAnalogAnalyzer {
public:
  GasAnalogAnalyzer();

  /**
   * @brief Ініціалізує аналізатор.
   * @param analogPin Пін, до якого підключено аналоговий вихід.
   * @param logCallback Функція для логування повідомлень.
   */
  void begin(uint8_t analogPin, std::function<void(String)> logCallback);

  /**
   * @brief Асинхронний обробник, який має викликатися в головному циклі loop().
   * @param now Поточний час в мілісекундах (від millis()).
   */
  void handle(unsigned long now);

  /**
   * @brief Повертає розраховану концентрацію етанолу.
   * @return Концентрація в ppm, 0.0f під час калібрації, -1.0f у випадку помилки.
   */
  float getEthanolPpm() const;

private:
  // --- Апаратні константи та налаштування ---
  static constexpr unsigned long ANALOG_POLLING_INTERVAL = 2500;
  static constexpr uint8_t OVERSAMPLING_COUNT = 10;
  static constexpr uint8_t CALIBRATION_SAMPLES_COUNT = 10;
  static constexpr float VOLTAGE_DIVIDER_RATIO = 0.66225f; // 10k / (10k + 5.1k)
  static constexpr float ADC_REF_VOLTAGE = 3.3f;
  static constexpr float ADC_MAX_VALUE = 4095.0f;
  static constexpr float LOAD_RESISTOR_OHMS = 10000.0f;

  // --- Внутрішні змінні стану ---
  uint8_t _pin;
  std::function<void(String)> _logCallback;

  float _ethanolPpm = 0.0f; // Початкове значення
  unsigned long _lastPollTime = 0;
  
  // --- Змінні для авто-калібрації ---
  unsigned int _calibSamples = 0;
  float _r0_sum = 0.0f;
  float _r0 = -1.0f; // Базовий опір, -1.0f означає, що калібрацію не пройдено
};

#endif // GAS_ANALOG_ANALYZER_H
