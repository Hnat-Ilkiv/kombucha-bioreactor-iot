#ifndef OneWireTemperatureManager_h
#define OneWireTemperatureManager_h

#include <Arduino.h>
#include "RemoteUpdateManager.h" // For LogCallback type

// Forward declarations for library classes
class OneWire;
class DallasTemperature;

class OneWireTemperatureManager {
public:
  typedef uint8_t DeviceAddress[8];

  OneWireTemperatureManager(uint8_t pin);
  ~OneWireTemperatureManager();

  void begin(RemoteUpdateManager::LogCallback logFunction);

  // --- Non-Blocking Flow Methods ---
  void requestTemperatures(); // Starts temperature conversion for all sensors
  float getSurfaceTemperature(); // Reads last conversion result by address
  float getLiquidTemperature();  // Reads last conversion result by address

private:
  uint8_t _pin;
  RemoteUpdateManager::LogCallback _logCtx;

  OneWire* _oneWire;
  DallasTemperature* _sensors;

  // Hardcoded hardware ROM addresses
  DeviceAddress _liquidSensorAddress;
  DeviceAddress _surfaceSensorAddress;

  static constexpr float SENSOR_FAULT_TEMPERATURE = -999.0f;
  static constexpr float MIN_PLAUSIBLE_TEMP = 0.0f;
  static constexpr float MAX_PLAUSIBLE_TEMP = 85.0f;

  // Private helper methods
  float readTempCByAddress(const DeviceAddress deviceAddress);
  void printAddress(DeviceAddress deviceAddress);
};

#endif