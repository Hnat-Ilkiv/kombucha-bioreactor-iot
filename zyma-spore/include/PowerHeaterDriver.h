#ifndef PowerHeaterDriver_h
#define PowerHeaterDriver_h

#include <Arduino.h>

/**
 * @class PowerHeaterDriver
 * @brief Manages a heating element using a non-blocking, low-frequency software PWM.
 * 
 * This driver simulates a PWM signal on a digital GPIO pin by manually controlling
 * the pin's state over a fixed time window (1Hz frequency). It is designed to
 * control high-power, slow-response systems like a heating bed, where high-frequency
 * hardware PWM is unnecessary.
 */
class PowerHeaterDriver {
public:
  /**
   * @brief Constructor.
   * @param pin The GPIO pin connected to the heater's MOSFET gate.
   */
  PowerHeaterDriver(uint8_t pin);

  /**
   * @brief Initializes the driver and the GPIO pin.
   */
  void begin();

  /**
   * @brief Sets the desired power level for the heater.
   * @param powerPercent The desired power from 0 (off) to 100 (full on).
   *                     Values outside this range will be clamped.
   */
  void setPowerPercent(int16_t powerPercent);

  /**
   * @brief Gets the currently set power level.
   * @return The current power level (0-100).
   */
  uint8_t getPowerPercent();

  /**
   * @brief The main non-blocking execution method.
   * This must be called on every iteration of the main loop() to update the
   * software PWM signal.
   */
  void handle();

  /**
   * @brief Performs an immediate, hardware-level shutdown of the heater.
   * This method provides a guaranteed off-state for emergency situations.
   */
  void emergencyHardwareShutdown();

private:
  uint8_t _pin;
  uint8_t _powerPercent;
  uint32_t _lastCycleMillis;
  
  static const uint32_t PWM_WINDOW_MS = 1000; // 1Hz PWM frequency
};

#endif
