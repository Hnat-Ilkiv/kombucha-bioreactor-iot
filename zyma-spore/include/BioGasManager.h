#ifndef BIO_GAS_MANAGER_H
#define BIO_GAS_MANAGER_H

#include <Arduino.h>
#include <Wire.h>
#include <functional>

/**
 * @class BioGasManager
 * @brief Асинхронний менеджер для роботи з цифровим датчиком TVOC (AGS02MA).
 * 
 * Клас інкапсулює логіку взаємодії з датчиком через I2C, використовуючи
 * неблокуючий підхід на основі millis() для опитування.
 */
class BioGasManager {
public:
  BioGasManager();

  /**
   * @brief Ініціалізує менеджер.
   * @param wireBus Посилання на об'єкт шини I2C (наприклад, Wire).
   * @param logCallback Функція для логування повідомлень.
   */
  void begin(TwoWire& wireBus, std::function<void(String)> logCallback);

  /**
   * @brief Асинхронний обробник, який має викликатися в головному циклі loop().
   * @param now Поточний час в мілісекундах (від millis()).
   */
  void handle(unsigned long now);

  /**
   * @brief Повертає останнє успішно зчитане значення TVOC з датчика AGS02MA.
   * @return Значення TVOC в ppm, або -1.0f у випадку помилки читання або CRC.
   */
  float getAgsTvoc() const;

private:
  /**
   * @brief Розраховує контрольну суму CRC-8 для заданого буфера.
   * @param buf Вказівник на масив даних.
   * @param len Довжина масиву.
   * @return Розрахована 8-бітна контрольна сума.
   */
  uint8_t calculateCRC8(uint8_t* buf, uint8_t len);

  // --- Апаратні константи та налаштування ---
  static constexpr uint8_t AGS02MA_ADDR = 0x1A;
  static constexpr unsigned long GAS_POLLING_INTERVAL = 2500; // Інтервал опитування
  static constexpr unsigned long SENSOR_READ_DELAY = 60; // Затримка після команди (згідно даташиту >30ms)

  // --- Внутрішні змінні стану ---
  TwoWire* _wire = nullptr;
  std::function<void(String)> _logCallback;

  float _tvoc = -1.0f; // Значення -1.0f означає помилку або початковий стан
  unsigned long _lastPollTime = 0;
  
  enum class State { IDLE, WAITING_FOR_DATA };
  State _state = State::IDLE;
};

#endif // BIO_GAS_MANAGER_H
