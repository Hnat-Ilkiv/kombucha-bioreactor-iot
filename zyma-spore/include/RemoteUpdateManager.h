#ifndef RemoteUpdateManager_h
#define RemoteUpdateManager_h

#include <Arduino.h>
#include <functional> // For std::function

// Forward-declare the driver class to avoid circular dependencies
class PowerHeaterDriver;

class RemoteUpdateManager {
public:
  // Use std::function for a more flexible and modern callback type
  using LogCallback = std::function<void(String)>;

  // Updated begin signature to accept dependencies
  void begin(const char* hostName, PowerHeaterDriver& heater, LogCallback logCallback);
  void handle();

private:
  // Non-static member to hold the logger for the instance
  LogCallback _logCallback;

  // Static pointer to the heater driver for use in static C-style callbacks
  static PowerHeaterDriver* _heaterInstance;
  static LogCallback _logCtx; // Static logger for callbacks

  // Static methods required by the ArduinoOTA library
  static void onStart();
  static void onEnd();
  static void onProgress(unsigned int progress, unsigned int total);
  static void onError(int error);
};

#endif