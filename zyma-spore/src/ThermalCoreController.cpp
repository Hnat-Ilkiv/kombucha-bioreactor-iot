#include "ThermalCoreController.h"
#include <math.h> // For exp()

ThermalCoreController::ThermalCoreController() {}

void ThermalCoreController::begin(PowerHeaterDriver& heater, NetworkMqttManager& net) {
  _heater = &heater;
  _net = &net;
}

void ThermalCoreController::update(unsigned long now, float target, bool processEnabled, float rawBed, float rawSurface, float rawLiquid) {
  if (!_heater || !_net) return; // Захист від виклику без ініціалізації

  // --- Крок 1: Фільтр фізичної реальності ---
  _filteredBed = rawBed;
  _filteredSurface = rawSurface;
  _filteredLiquid = rawLiquid;

  // Hardware Reality Filter: Anything outside 0.0C - 80.0C is a hardware ghost or disconnect
  if (_filteredBed < 0.0f || _filteredBed > 80.0f) _filteredBed = -999.0f;
  if (_filteredSurface < 0.0f || _filteredSurface > 80.0f) _filteredSurface = -999.0f;
  if (_filteredLiquid < 0.0f || _filteredLiquid > 80.0f) _filteredLiquid = -999.0f;

  // --- Крок 2: Матриця Fail-Safe арбітражу з обмеженим логуванням ---
  bool hardwareFault = false;

  // Контур 1: Нагрівальний стіл (NTC)
  if (_filteredBed == -999.0f) {
    hardwareFault = true;
    if (!_faultLogged_bedDisconnect) {
      _net->logDebug("FAULT: Contour 1 (NTC Bed) Sensor Disconnected!");
      _faultLogged_bedDisconnect = true;
    }
  } else {
    _faultLogged_bedDisconnect = false;
    if (_filteredBed > MAX_SAFE_BED_TEMP) {
      hardwareFault = true;
      if (!_faultLogged_bedOverheat) {
        _net->logDebug("EMERGENCY: Bed Overheat!");
        _faultLogged_bedOverheat = true;
      }
    } else {
      _faultLogged_bedOverheat = false;
    }
  }

  // Контур 2: Поверхня (DS18B20)
  if (_filteredSurface == -999.0f) {
    hardwareFault = true;
    if (!_faultLogged_surfaceDisconnect) {
      _net->logDebug("FAULT: Contour 2 (DS18B20 Surface) Sensor Disconnected!");
      _faultLogged_surfaceDisconnect = true;
    }
  } else {
    _faultLogged_surfaceDisconnect = false;
    if (_filteredSurface > MAX_SAFE_SURFACE_TEMP) {
      hardwareFault = true;
      if (!_faultLogged_surfaceOverheat) {
        _net->logDebug("EMERGENCY: Surface Overheat!");
        _faultLogged_surfaceOverheat = true;
      }
    } else {
      _faultLogged_surfaceOverheat = false;
    }
  }

  // Контур 3: Рідина (DS18B20)
  if (_filteredLiquid == -999.0f) {
    hardwareFault = true;
    if (!_faultLogged_liquidDisconnect) {
      _net->logDebug("FAULT: Contour 3 (DS18B20 Liquid) Sensor Disconnected!");
      _faultLogged_liquidDisconnect = true;
    }
  } else {
    _faultLogged_liquidDisconnect = false;
    if (_filteredLiquid > MAX_SAFE_LIQUID_TEMP) {
      hardwareFault = true;
      if (!_faultLogged_liquidOverheat) {
        _net->logDebug("EMERGENCY: SCOBY Biological Lethal Overheat! Shutting down.");
        _faultLogged_liquidOverheat = true;
      }
    } else {
      _faultLogged_liquidOverheat = false;
    }
  }

  // --- Крок 3: Розрахунок та застосування керуючої потужності ---
  if (hardwareFault || !processEnabled) {
    _heater->setPowerPercent(0);
  } else {
    // --- Multiplicative Non-linear Thermal Attenuation Controller ---
    float liquidError = target - _filteredLiquid;
    float basePower = (liquidError > 0.0f) ? (MAX_PRODUCTION_POWER * (1.0f - exp(-0.7f * liquidError))) : 0.0f;
    
    float deltaBed = _filteredBed - 35.0f;
    float normBed = (deltaBed > 0.0f) ? (deltaBed / (55.0f - 35.0f)) : 0.0f;
    float psiBed = (normBed < 1.0f) ? (1.0f - normBed * normBed) : 0.0f;
    
    float deltaSurf = _filteredSurface - 30.0f;
    float normSurf = (deltaSurf > 0.0f) ? (deltaSurf / (45.0f - 30.0f)) : 0.0f;
    float psiSurface = (normSurf < 1.0f) ? (1.0f - normSurf * normSurf) : 0.0f;
    
    float finalPower = basePower * psiBed * psiSurface;
    
    _heater->setPowerPercent((int16_t)finalPower);
  }
}

float ThermalCoreController::getFilteredBed() const {
  return _filteredBed;
}

float ThermalCoreController::getFilteredSurface() const {
  return _filteredSurface;
}

float ThermalCoreController::getFilteredLiquid() const {
  return _filteredLiquid;
}
