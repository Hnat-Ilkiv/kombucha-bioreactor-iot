#include "AmbientEnvManager.h"

AmbientEnvManager::AmbientEnvManager()
  : _currentState(IDLE),
    _wire(nullptr),
    _logCallback(nullptr),
    _lastCycleStart(0),
    _measurementStart(0),
    _ambientTemperature(SENSOR_FAULT_VALUE),
    _ambientHumidity(SENSOR_FAULT_VALUE) {
}

void AmbientEnvManager::begin(TwoWire& wireBus, LogCallback logCallback) {
  _wire = &wireBus;
  _logCallback = logCallback;
  resetSensor(); // Perform a soft reset on startup
}

void AmbientEnvManager::handle() {
  unsigned long now = millis();

  switch (_currentState) {
    case IDLE: {
      if (now - _lastCycleStart >= ENV_POLLING_INTERVAL) {
        _wire->beginTransmission(I2C_ADDR);
        _wire->write(CMD_TRIG_TEMP_NO_HOLD);
        if (_wire->endTransmission() == 0) {
          _measurementStart = now;
          _currentState = WAIT_TEMP;
        } else {
          if (_logCallback) _logCallback("HTU21D | Failed to send temp command.");
          resetSensor(); // Reset on I2C error
        }
      }
      break;
    }
    case WAIT_TEMP: {
      if (now - _measurementStart >= MEASUREMENT_WAIT_MS) {
        uint8_t buffer[3];
        if (_wire->requestFrom(I2C_ADDR, (uint8_t)3) == 3) {
          buffer[0] = _wire->read(); // MSB
          buffer[1] = _wire->read(); // LSB
          buffer[2] = _wire->read(); // CRC

          if (crc8(buffer, 2) == buffer[2]) {
            uint16_t rawValue = ((uint16_t)buffer[0] << 8) | (buffer[1] & 0xFC);
            _ambientTemperature = -46.85f + 175.72f * (float)rawValue / 65536.0f;

            // Immediately trigger humidity measurement
            _wire->beginTransmission(I2C_ADDR);
            _wire->write(CMD_TRIG_HUMID_NO_HOLD);
            if (_wire->endTransmission() == 0) {
              _measurementStart = now;
              _currentState = WAIT_HUMID;
            } else {
              resetSensor(); // Reset on error
            }
          } else {
            if (_logCallback) _logCallback("HTU21D | Temp CRC mismatch.");
            resetSensor();
          }
        } else {
          if (_logCallback) _logCallback("HTU21D | Failed to read temp data.");
          resetSensor();
        }
      }
      break;
    }
    case WAIT_HUMID: {
      if (now - _measurementStart >= MEASUREMENT_WAIT_MS) {
        uint8_t buffer[3];
        if (_wire->requestFrom(I2C_ADDR, (uint8_t)3) == 3) {
          buffer[0] = _wire->read(); // MSB
          buffer[1] = _wire->read(); // LSB
          buffer[2] = _wire->read(); // CRC

          if (crc8(buffer, 2) == buffer[2]) {
            uint16_t rawValue = ((uint16_t)buffer[0] << 8) | (buffer[1] & 0xFC);
            _ambientHumidity = -6.0f + 125.0f * (float)rawValue / 65536.0f;
          } else {
            if (_logCallback) _logCallback("HTU21D | Humid CRC mismatch.");
            _ambientHumidity = SENSOR_FAULT_VALUE;
          }
        } else {
          if (_logCallback) _logCallback("HTU21D | Failed to read humid data.");
          _ambientHumidity = SENSOR_FAULT_VALUE;
        }
        resetSensor(); // Return to IDLE state for next cycle
      }
      break;
    }
  }
}

float AmbientEnvManager::getAmbientTemperature() {
  return _ambientTemperature;
}

float AmbientEnvManager::getAmbientHumidity() {
  return _ambientHumidity;
}

void AmbientEnvManager::resetSensor() {
  _currentState = IDLE;
  _lastCycleStart = millis();
}

uint8_t AmbientEnvManager::crc8(const uint8_t* data, int len) {
  const uint8_t poly = 0x31; // CRC-8 polynomial for HTU21D (x^8 + x^5 + x^4 + 1)
  uint8_t crc = 0;
  for (int j = len; j; --j) {
    crc ^= *data++;
    for (int i = 8; i; --i) {
      crc = (crc & 0x80) ? (crc << 1) ^ poly : (crc << 1);
    }
  }
  return crc;
}
