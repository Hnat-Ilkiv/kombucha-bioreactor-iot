#ifndef NETWORK_MQTT_MANAGER_H
#define NETWORK_MQTT_MANAGER_H

#include <Arduino.h>
#include <functional>
#include <WiFi.h>
#include <PubSubClient.h>

constexpr unsigned long RECONNECT_INTERVAL = 5000;

class NetworkMqttManager {
public:
  // --- MQTT TOPIC SUFFIXES (STATIC CONSTEXPR TO PREVENT LINKER ERRORS) ---
  static constexpr const char* SUFFIX_DEBUG = "system/debug";
  static constexpr const char* SUFFIX_STATUS = "system/status";
  static constexpr const char* SUFFIX_CONTROL = "control/target_set";
  static constexpr const char* SUFFIX_TEMP_BED = "sensors/bed_temp_c";
  static constexpr const char* SUFFIX_TEMP_SURFACE = "sensors/surface_temp_c";
  static constexpr const char* SUFFIX_TEMP_LIQUID = "sensors/liquid_temp_c";
  static constexpr const char* SUFFIX_TEMP_AMBIENT = "sensors/ambient_temp_c";
  static constexpr const char* SUFFIX_HUMID_AMBIENT = "sensors/ambient_humid_pct";
  static constexpr const char* SUFFIX_GAS_DIGITAL = "sensors/digital_tvoc_ppm";
  static constexpr const char* SUFFIX_GAS_ANALOG = "sensors/analog_ethanol_ppm";
  static constexpr const char* SUFFIX_HEATER_POWER = "sensors/heater_power_pct";
  static constexpr const char* SUFFIX_RUN_SET = "control/run_set";
  static constexpr const char* SUFFIX_PROCESS_STATE = "sensors/process_state";

  NetworkMqttManager();
  void begin(const char* ssid, const char* pass, const char* mqttServer, int port, 
             std::function<void(float)> onTargetTempReceived,
             std::function<void(bool)> onRunStateReceived);
  void handle(unsigned long now, std::function<void()> preBlockShutoff);
  void publishTelemetry(const char* topicSuffix, float value);
  void logDebug(String message);
  bool connected();

private:
  WiFiClient _espClient;
  PubSubClient _client;
  
  char _baseTopicPrefix[32];
  const char* _mqtt_server;
  int _mqtt_port;
  unsigned long _lastReconnectAttempt = 0;
  
  std::function<void(float)> _onTargetTempReceived;
  std::function<void(bool)> _onRunStateReceived;
  
  void reconnect();
  void mqttCallback(char* topic, byte* payload, unsigned int length);
};

#endif // NETWORK_MQTT_MANAGER_H
