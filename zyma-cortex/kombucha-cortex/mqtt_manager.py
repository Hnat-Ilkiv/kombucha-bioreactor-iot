import threading
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from config import MQTT_BROKER_HOST, MQTT_BROKER_PORT


class MQTTManager:
    """A clean, isolated, object-oriented MQTT communication manager."""

    def __init__(
        self,
        on_telemetry_received: Optional[
            Callable[[str, str, float], None]
        ] = None,
    ):
        """
        Initializes the MQTT manager.

        Args:
            on_telemetry_received: An optional callback hook function
                `on_telemetry_received(mac_address, metric_name, value)`.
        """
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self._on_telemetry_received = on_telemetry_received
        self._publish_lock = threading.Lock()

    def connect(self):
        """Connects to the MQTT broker and starts the network loop."""
        self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Internal callback for when the client connects to the broker."""
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe("kombucha/#")
        else:
            print(f"Failed to connect, return code {rc}\n")

    def _on_message(self, client, userdata, msg):
        """Internal callback for when a message is received from the broker."""
        try:
            topic_parts = msg.topic.split("/")
            if len(topic_parts) < 3:
                return

            mac_address = topic_parts[1].upper()
            metric_name = topic_parts[-1]

            if mac_address in ("SYSTEM", "HUB"):
                return

            if self._on_telemetry_received:
                payload_value = float(msg.payload.decode("utf-8"))
                self._on_telemetry_received(
                    mac_address, metric_name, payload_value
                )

        except (ValueError, IndexError) as e:
            # Gracefully swallow malformed data logs
            # print(f"Error processing message on topic {msg.topic}: {e}")
            pass

    def send_run_state(self, mac_address: str, state: bool):
        """
        Sends a run state command to a specific device.

        Args:
            mac_address: The MAC address of the target device.
            state: The desired run state (True for run, False for stop).
        """
        topic = f"kombucha/{mac_address}/control/run_set"
        payload = "1" if state else "0"
        with self._publish_lock:
            self.client.publish(topic, payload, qos=1)

    def send_target_temperature(self, mac_address: str, temp: float):
        """
        Sends a target temperature command to a specific device.

        Args:
            mac_address: The MAC address of the target device.
            temp: The target temperature (must be between 18.0 and 29.0).
        """
        assert 18.0 <= temp <= 29.0, "Target temperature out of safe range."
        topic = f"kombucha/{mac_address}/control/target_set"
        payload = str(round(temp, 1))
        with self._publish_lock:
            self.client.publish(topic, payload, qos=1)