#include "RemoteUpdateManager.h"
#include "PowerHeaterDriver.h" // Include the full header for the driver
#include <ArduinoOTA.h>

// Initialize static members
RemoteUpdateManager::LogCallback RemoteUpdateManager::_logCtx = nullptr;
PowerHeaterDriver* RemoteUpdateManager::_heaterInstance = nullptr;

void RemoteUpdateManager::begin(const char* hostName, PowerHeaterDriver& heater, LogCallback logCallback) {
  // Store the logger and a pointer to the heater instance for static callbacks
  _logCtx = logCallback;
  _heaterInstance = &heater;
  _logCallback = logCallback; // Also store in non-static member if needed elsewhere

  ArduinoOTA.setHostname(hostName);

  // Set up all OTA callbacks
  ArduinoOTA.onStart(onStart); // onStart will now handle the shutdown
  ArduinoOTA.onEnd(onEnd);
  ArduinoOTA.onProgress(onProgress);
  ArduinoOTA.onError([](ota_error_t error) {
    onError(error);
  });

  ArduinoOTA.begin();
}

void RemoteUpdateManager::handle() {
  ArduinoOTA.handle();
}

void RemoteUpdateManager::onStart() {
  // This is a static method, so it must use the static member pointers
  if (_logCtx) {
    _logCtx("OTA Update Started. EMERGENCY SHUTDOWN of heater.");
  }
  if (_heaterInstance) {
    _heaterInstance->emergencyHardwareShutdown();
  }
}

void RemoteUpdateManager::onEnd() {
  if (_logCtx) {
    _logCtx("OTA Update Finished. Rebooting...");
  }
}

void RemoteUpdateManager::onProgress(unsigned int progress, unsigned int total) {
  if (_logCtx && total > 0) {
    unsigned int percentage = (progress * 100) / total;
    String message = "OTA Progress: " + String(percentage) + "%";
    _logCtx(message);
  }
}

void RemoteUpdateManager::onError(int error) {
  if (_logCtx) {
    String message = "OTA Error: ";
    if (error == OTA_AUTH_ERROR) message += "Auth Failed";
    else if (error == OTA_BEGIN_ERROR) message += "Begin Failed";
    else if (error == OTA_CONNECT_ERROR) message += "Connect Failed";
    else if (error == OTA_RECEIVE_ERROR) message += "Receive Failed";
    else if (error == OTA_END_ERROR) message += "End Failed";
    else message += "Unknown Error";
    _logCtx(message);
  }
}