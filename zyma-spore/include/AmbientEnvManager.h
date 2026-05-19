#ifndef AmbientEnvManager_h
#define AmbientEnvManager_h

#include <Arduino.h>
#include <functional>
#include <Wire.h>

/**
 * @class AmbientEnvManager
 * @brief Manages an HTU21D I2C sensor using a non-blocking asynchronous state machine.
 */
class AmbientEnvManager {
public:
  using LogCallback = std::function<void(String)>;

  AmbientEnvManager();

  /**
   * @brief Initializes the manager with the I2C bus and a logger callback.
   * @param wireBus A reference to the TwoWire instance (e.g., Wire).
   * @param logCallback A function to handle logging.
   */
  void begin(TwoWire& wireBus, LogCallback logCallback);

  /**
   * @brief Executes the state machine. Must be called in the main loop().
   */
  void handle();

  /**
   * @brief Gets the last valid ambient temperature reading.
   * @return Temperature in Celsius, or -999.0f on fault.
   */
  float getAmbientTemperature();

  /**
   * @brief Gets the last valid ambient humidity reading.
   * @return Relative humidity in %, or -999.0f on fault.
   */
  float getAmbientHumidity();

private:
  enum State { IDLE, WAIT_TEMP, WAIT_HUMID };

  State _currentState;
  TwoWire* _wire;
  LogCallback _logCallback;

  unsigned long _lastCycleStart;
  unsigned long _measurementStart;

  float _ambientTemperature;
  float _ambientHumidity;

  static constexpr uint8_t I2C_ADDR = 0x40;
  static constexpr unsigned long ENV_POLLING_INTERVAL = 2500;
  static constexpr unsigned long MEASUREMENT_WAIT_MS = 50;
  static constexpr float SENSOR_FAULT_VALUE = -999.0f;
  
  // HTU21D Commands
  static constexpr uint8_t CMD_TRIG_TEMP_NO_HOLD = 0xF3;
  static constexpr uint8_t CMD_TRIG_HUMID_NO_HOLD = 0xF5;
  static constexpr uint8_t CMD_SOFT_RESET = 0xFE;

  uint8_t crc8(const uint8_t* data, int len);
  void resetSensor();
};

#endif
