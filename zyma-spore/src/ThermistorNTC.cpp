#include "ThermistorNTC.h"
#include <math.h> // For log()

// Constructor implementation
ThermistorNTC::ThermistorNTC(uint8_t pin, float beta, float nominalResistance, float seriesResistor, float calibrationOffset)
  : _pin(pin),
    _beta(beta),
    _nominalResistance(nominalResistance),
    _seriesResistor(seriesResistor),
    _calibrationOffset(calibrationOffset),
    _filteredTemperature(-999.0f) { // Initialize filter state
}

// Initialization method
void ThermistorNTC::begin() {
  pinMode(_pin, INPUT);
}

// Method to read temperature in Celsius
float ThermistorNTC::readTemperatureCelsius() {
  // 1. Multi-sampling to reduce ADC noise
  float analogValueSum = 0;
  for (uint8_t i = 0; i < _numSamples; ++i) {
    analogValueSum += analogRead(_pin);
    delay(2); // Small delay for stability
  }
  float averageAnalogValue = analogValueSum / _numSamples;

  // 2. Electrical Fault Guard Clause
  if (averageAnalogValue <= 0.0 || averageAnalogValue >= _adcMax) {
    return _errorTemperature;
  }

  // 3. Ratiometric Resistance Calculation
  float ntcResistance = _seriesResistor * ((_adcMax / averageAnalogValue) - 1.0);
  if (ntcResistance <= 0) {
      return _errorTemperature;
  }

  // 4. Beta Equation for Temperature Conversion
  float T0_K = _nominalTemperature + 273.15;
  float steinhart = log(ntcResistance / _nominalResistance);
  steinhart /= _beta;
  steinhart += 1.0 / T0_K;
  float rawCalculatedTemp = 1.0 / steinhart - 273.15;

  // 5. Plausibility Check
  if (rawCalculatedTemp < 0.0f || rawCalculatedTemp > 85.0f) {
    return _errorTemperature;
  }

  // 6. Apply EMA (Exponential Moving Average) low-pass filter
  const float alpha = 0.15f;
  if (_filteredTemperature == -999.0f) {
    // Prime the filter with the first valid reading
    _filteredTemperature = rawCalculatedTemp;
  } else {
    // Apply EMA formula
    _filteredTemperature = (alpha * rawCalculatedTemp) + ((1.0f - alpha) * _filteredTemperature);
  }

  // 7. Return filtered value with calibration offset
  return _filteredTemperature + _calibrationOffset;
}
