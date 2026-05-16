#include "GasAnalogAnalyzer.h"
#include <math.h>

GasAnalogAnalyzer::GasAnalogAnalyzer() {}

void GasAnalogAnalyzer::begin(uint8_t analogPin, std::function<void(String)> logCallback) {
  _pin = analogPin;
  _logCallback = logCallback;
  _lastPollTime = millis();
}

void GasAnalogAnalyzer::handle(unsigned long now) {
  if (now - _lastPollTime >= ANALOG_POLLING_INTERVAL) {
    _lastPollTime = now;

    // --- Крок 1: Оверсемплінг для стабілізації ---
    uint32_t totalAdc = 0;
    for (uint8_t i = 0; i < OVERSAMPLING_COUNT; i++) {
      totalAdc += analogRead(_pin);
      delayMicroseconds(50);
    }
    float avgAdc = (float)totalAdc / OVERSAMPLING_COUNT;

    // --- Крок 2: Розрахунок напруги та опору ---
    float voltageAtEsp = (avgAdc / ADC_MAX_VALUE) * ADC_REF_VOLTAGE;
    float vOutSensor = voltageAtEsp / VOLTAGE_DIVIDER_RATIO;

    // Захист від некоректних значень
    if (vOutSensor >= 4.95f) { // Перевірка тільки на високовольтне замикання
      _ethanolPpm = -1.0f;
      if (_logCallback) _logCallback("GasAnalog | MiCS-5524 short circuit fault: " + String(vOutSensor) + "V");
      return;
    }

    float rs;
    if (vOutSensor <= 0.04f) { // Обробка 0.00V як чистого повітря, встановлюючи RS до максимуму
       rs = 1000000.0f; // Встановити максимум 1 MOhm для чистого повітря
    } else {
       rs = LOAD_RESISTOR_OHMS * (5.0f - vOutSensor) / vOutSensor;
    }

    // --- Крок 3: Фаза калібрації або розрахунку PPM ---
    if (_calibSamples < CALIBRATION_SAMPLES_COUNT) {
      // Фаза калібрації: накопичуємо значення для R0
      _r0_sum += rs;
      _calibSamples++;
      _ethanolPpm = 0.0f; // Сигнал, що йде калібрація

      if (_calibSamples >= CALIBRATION_SAMPLES_COUNT) {
        _r0 = _r0_sum / CALIBRATION_SAMPLES_COUNT;
        if (_logCallback) {
          _logCallback("GasAnalog | MiCS-5524 calibrated with R0 = " + String(_r0) + " Ohms");
        }
      }
    } else {
      // Фаза розрахунку: R0 вже відомий
      if (_r0 > 0) {
        float ratio = rs / _r0;
        _ethanolPpm = 10.0f * pow(ratio, -1.48f);
      } else {
        // Помилка: R0 не було встановлено
        _ethanolPpm = -1.0f;
      }
    }
  }
}

float GasAnalogAnalyzer::getEthanolPpm() const {
  return _ethanolPpm;
}
