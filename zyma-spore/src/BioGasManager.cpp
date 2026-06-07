#include "BioGasManager.h"

BioGasManager::BioGasManager() {}

void BioGasManager::begin(TwoWire& wireBus, std::function<void(String)> logCallback) {
  _wire = &wireBus;
  _logCallback = logCallback;
  _lastPollTime = millis(); // Ініціалізація для першого запиту, щоб уникнути миттєвого спрацювання
}

void BioGasManager::handle(unsigned long now) {
  if (!_wire) return;

  // State 1: Якщо час настав, ініціюємо читання
  if (_state == State::IDLE && (now - _lastPollTime >= GAS_POLLING_INTERVAL)) {
    _wire->beginTransmission(AGS02MA_ADDR);
    _wire->write(0x00); // Команда на читання TVOC
    uint8_t error = _wire->endTransmission();
    
    if (error == 0) {
      _lastPollTime = now; // Оновлюємо час останньої *успішної* команди
      _state = State::WAITING_FOR_DATA;
    } else {
      _tvoc = -1.0f;
      if (_logCallback) {
        _logCallback("BioGas | AGS02MA I2C transmission failed with code: " + String(error));
      }
      // Скидаємо таймер, щоб спробувати знову через повний інтервал
      _lastPollTime = now;
    }
  }

  // State 2: Якщо ми очікуємо дані і пройшло достатньо часу, зчитуємо їх
  if (_state == State::WAITING_FOR_DATA && (now - _lastPollTime > SENSOR_READ_DELAY)) {
    uint8_t buffer[5] = {0};
    uint8_t bytesRead = _wire->requestFrom(AGS02MA_ADDR, (uint8_t)5);

    if (bytesRead == 5) {
      for (uint8_t i = 0; i < 5; i++) {
        buffer[i] = _wire->read();
      }

      // Тепер виконуємо валідацію реальних даних
      if (calculateCRC8(buffer, 4) == buffer[4]) {
        // Екстракція 24-бітного значення TVOC з Data2, Data3 та Data4
        uint32_t tvoc_raw = ((uint32_t)buffer[1] << 16) | ((uint32_t)buffer[2] << 8) | buffer[3];
        _tvoc = (float)tvoc_raw;
      } else {
        _tvoc = -1.0f;
        if (_logCallback) {
          _logCallback("BioGas | CRC Fail! Raw Bytes: 0x" + String(buffer[0], HEX) + 
                       " 0x" + String(buffer[1], HEX) + " 0x" + String(buffer[2], HEX) + 
                       " 0x" + String(buffer[3], HEX) + " 0x" + String(buffer[4], HEX));
        }
      }
    } else {
      _tvoc = -1.0f;
      if (_logCallback) {
        _logCallback("BioGas | AGS02MA I2C read failed. Expected 5 bytes, got " + String(bytesRead));
      }
    }
    _state = State::IDLE; // Повертаємось у стан очікування
  }
}

float BioGasManager::getAgsTvoc() const {
  return _tvoc / 1000.0;
}

uint8_t BioGasManager::calculateCRC8(uint8_t* data, uint8_t len) {
  uint8_t crc = 0xFF; // Початкове значення
  for (uint8_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (uint8_t j = 0; j < 8; j++) {
      if (crc & 0x80) {
        crc = (crc << 1) ^ 0x31; // Поліном 0x31
      } else {
        crc <<= 1;
      }
    }
  }
  return crc;
}
