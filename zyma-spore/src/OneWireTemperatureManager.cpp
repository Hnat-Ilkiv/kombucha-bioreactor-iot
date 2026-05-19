#include "OneWireTemperatureManager.h"
#include <OneWire.h>
#include <DallasTemperature.h>

OneWireTemperatureManager::OneWireTemperatureManager(uint8_t pin) 
  : _pin(pin), _logCtx(nullptr) {
  _oneWire = new OneWire(_pin);
  _sensors = new DallasTemperature(_oneWire);

  // Hardcode the real ROM addresses based on thermal tests
  const DeviceAddress liquidAddr  = { 0x28, 0x21, 0x66, 0x31, 0x39, 0x6A, 0xF5, 0x73 };
  const DeviceAddress surfaceAddr = { 0x28, 0x61, 0x67, 0x31, 0x39, 0x5E, 0xB1, 0xFA };
  
  memcpy(_liquidSensorAddress, liquidAddr, sizeof(DeviceAddress));
  memcpy(_surfaceSensorAddress, surfaceAddr, sizeof(DeviceAddress));
}

OneWireTemperatureManager::~OneWireTemperatureManager() {
  delete _sensors;
  delete _oneWire;
}

void OneWireTemperatureManager::begin(RemoteUpdateManager::LogCallback logFunction) {
  _logCtx = logFunction;
  _sensors->begin();
  
  // Set non-blocking mode
  _sensors->setWaitForConversion(false);
  
  if (_logCtx) {
    _logCtx("OneWire | Initialized on GPIO " + String(_pin) + ". Mode: Address-based, Non-Blocking.");
    _logCtx("OneWire | Liquid Sensor Address: 28216631396AF573");
    _logCtx("OneWire | Surface Sensor Address: 28616731395EB1FA");
  }
}

void OneWireTemperatureManager::requestTemperatures() {
  _sensors->requestTemperatures();
}

float OneWireTemperatureManager::getSurfaceTemperature() {
  return readTempCByAddress(_surfaceSensorAddress);
}

float OneWireTemperatureManager::getLiquidTemperature() {
  return readTempCByAddress(_liquidSensorAddress);
}

// --- Private Helper Methods ---

float OneWireTemperatureManager::readTempCByAddress(const DeviceAddress deviceAddress) {
  // getTempC reads the result from the last non-blocking request
  float tempC = _sensors->getTempC(deviceAddress);

  // Hardware and Plausibility Guards
  if (tempC == -127.0f || tempC < MIN_PLAUSIBLE_TEMP || tempC > MAX_PLAUSIBLE_TEMP) {
    return SENSOR_FAULT_TEMPERATURE;
  }
  
  return tempC;
}

void OneWireTemperatureManager::printAddress(DeviceAddress deviceAddress) {
  // This helper is no longer used for periodic logging but can be kept for diagnostics if needed.
  // For now, it's removed to clean up the code as requested.
}