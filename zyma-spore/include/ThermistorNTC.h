#ifndef ThermistorNTC_h
#define ThermistorNTC_h

#include <Arduino.h>

class ThermistorNTC {
public:
  // Constructor: Initializes with physical properties and a calibration offset
  ThermistorNTC(uint8_t pin, float beta, float nominalResistance, float seriesResistor, float calibrationOffset);

  // Initializes the ADC for reading
  void begin();

  // Reads, filters, and returns the current temperature in Celsius
  float readTemperatureCelsius();

private:
  uint8_t _pin;
  float _beta;
  float _nominalResistance;
  float _seriesResistor;
  float _calibrationOffset; // Software calibration offset

  // EMA Filter state
  float _filteredTemperature;

  const float _nominalTemperature = 25.0;
  const float _adcMax = 4095.0;
  const uint8_t _numSamples = 10;
  const float _errorTemperature = -999.0f;
};

#endif