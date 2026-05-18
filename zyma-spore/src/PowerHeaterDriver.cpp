#include "PowerHeaterDriver.h"

PowerHeaterDriver::PowerHeaterDriver(uint8_t pin)
  : _pin(pin),
    _powerPercent(0),
    _lastCycleMillis(0) {
}

void PowerHeaterDriver::begin() {
  pinMode(_pin, OUTPUT);
  digitalWrite(_pin, LOW); // Ensure heater is off at startup
}

void PowerHeaterDriver::setPowerPercent(int16_t powerPercent) {
  if (powerPercent < 0) {
    _powerPercent = 0; // Reliably handle negative inputs by clamping to zero
  } else if (powerPercent > 100) {
    _powerPercent = 100; // Clamp oversized values
  } else {
    _powerPercent = (uint8_t)powerPercent; // Safely cast to internal type
  }
}

uint8_t PowerHeaterDriver::getPowerPercent() {
  return _powerPercent;
}

void PowerHeaterDriver::handle() {
  uint32_t currentMillis = millis();

  // Check if a new PWM cycle should start
  if (currentMillis - _lastCycleMillis >= PWM_WINDOW_MS) {
    _lastCycleMillis = currentMillis;
  }

  // Calculate the time the pin should be HIGH in this cycle
  uint32_t highTime = (PWM_WINDOW_MS * _powerPercent) / 100;

  // Determine the pin state based on the elapsed time in the current cycle
  if (_powerPercent > 0 && (currentMillis - _lastCycleMillis < highTime)) {
    digitalWrite(_pin, HIGH);
  } else {
    digitalWrite(_pin, LOW);
  }
}

void PowerHeaterDriver::emergencyHardwareShutdown() {
  // 1. Set logical power to 0
  setPowerPercent(0);
  // 2. Force an immediate update of the PWM logic to reflect 0% power
  handle();
  // 3. Perform a direct hardware write as a final guarantee to ground the MOSFET gate
  digitalWrite(_pin, LOW);
}