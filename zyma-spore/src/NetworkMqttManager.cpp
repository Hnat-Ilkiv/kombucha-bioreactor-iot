#include "NetworkMqttManager.h"
#include "secrets.h"

NetworkMqttManager::NetworkMqttManager() : _client(_espClient) {}

void NetworkMqttManager::begin(const char* ssid, const char* pass, const char* mqttServer, int port, 
                             std::function<void(float)> onTargetTempReceived,
                             std::function<void(bool)> onRunStateReceived) {
  _mqtt_server = mqttServer;
  _mqtt_port = port;
  _onTargetTempReceived = onTargetTempReceived;
  _onRunStateReceived = onRunStateReceived;

  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  // --- Dynamic Base Topic Generation ---
  String mac = WiFi.macAddress();
  mac.replace(":", "");
  snprintf(_baseTopicPrefix, sizeof(_baseTopicPrefix), "kombucha/%s/", mac.c_str());

  _client.setServer(_mqtt_server, _mqtt_port);
  _client.setCallback([this](char* topic, byte* payload, unsigned int length) {
    this->mqttCallback(topic, payload, length);
  });

  reconnect();
}

void NetworkMqttManager::handle(unsigned long now, std::function<void()> preBlockShutoff) {
  if (!_client.connected()) {
    if (now - _lastReconnectAttempt >= RECONNECT_INTERVAL) {
      _lastReconnectAttempt = now;
      if (WiFi.status() != WL_CONNECTED) return;
      
      // --- UNCONDITIONAL PRE-BLOCKING SAFETY VALVE ---
      // Force weapon-grade safety: shut down the power stage before freezing execution!
      if (preBlockShutoff) {
        preBlockShutoff();
      }
      
      reconnect();
    }
  }
  _client.loop();
}

bool NetworkMqttManager::connected() {
  return _client.connected();
}

void NetworkMqttManager::publishTelemetry(const char* topicSuffix, float value) {
  if (connected()) {
    char fullTopic[64];
    snprintf(fullTopic, sizeof(fullTopic), "%s%s", _baseTopicPrefix, topicSuffix);
    
    char buffer[10];
    dtostrf(value, 4, 2, buffer);
    _client.publish(fullTopic, buffer);
  }
}

void NetworkMqttManager::logDebug(String message) {
  if (connected()) {
    char fullTopic[64];
    snprintf(fullTopic, sizeof(fullTopic), "%s%s", _baseTopicPrefix, SUFFIX_DEBUG);
    _client.publish(fullTopic, message.c_str());
  }
}

void NetworkMqttManager::reconnect() {
  String mac = WiFi.macAddress();
  mac.replace(":", "");
  String clientId = "ZymaSpore-" + mac;

  char statusTopic[64];
  snprintf(statusTopic, sizeof(statusTopic), "%s%s", _baseTopicPrefix, SUFFIX_STATUS);

  if (_client.connect(clientId.c_str(), statusTopic, 1, true, "offline")) {
    logDebug("MQTT connected with Client ID: " + clientId);
    _client.publish(statusTopic, (const uint8_t*)"online", 6, true);

    char tempControlTopic[64];
    snprintf(tempControlTopic, sizeof(tempControlTopic), "%s%s", _baseTopicPrefix, SUFFIX_CONTROL);
    _client.subscribe(tempControlTopic);

    char runControlTopic[64];
    snprintf(runControlTopic, sizeof(runControlTopic), "%s%s", _baseTopicPrefix, SUFFIX_RUN_SET);
    _client.subscribe(runControlTopic);
  }
}

void NetworkMqttManager::mqttCallback(char* topic, byte* payload, unsigned int length) {
  char expectedTempControlTopic[64];
  snprintf(expectedTempControlTopic, sizeof(expectedTempControlTopic), "%s%s", _baseTopicPrefix, SUFFIX_CONTROL);

  char expectedRunControlTopic[64];
  snprintf(expectedRunControlTopic, sizeof(expectedRunControlTopic), "%s%s", _baseTopicPrefix, SUFFIX_RUN_SET);

  String message;
  message.reserve(length);
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  if (strcmp(topic, expectedTempControlTopic) == 0) {
    float parsedValue = message.toFloat();
    if (parsedValue >= 18.0f && parsedValue <= 29.0f) {
      if (_onTargetTempReceived) _onTargetTempReceived(parsedValue);
      logDebug("Control | New target temperature received: " + String(parsedValue, 2) + "C");
    } else {
      logDebug("Control | Ignored invalid target temperature: " + message);
    }
  } else if (strcmp(topic, expectedRunControlTopic) == 0) {
    if (message == "1") {
      if (_onRunStateReceived) _onRunStateReceived(true);
      logDebug("Control | Process RUN command received.");
    } else if (message == "0") {
      if (_onRunStateReceived) _onRunStateReceived(false);
      logDebug("Control | Process STOP command received.");
    } else {
      logDebug("Control | Ignored invalid process run state: " + message);
    }
  }
}
