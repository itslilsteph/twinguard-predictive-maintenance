"""
mqtt_test.py

This is a simple testing script used to simulate an MQTT data publisher.

It sends a sample vibration payload to the MQTT broker topic used by the main system.
This helps verify that:
1. The MQTT broker connection is working
2. The subscriber (main application) can receive data correctly
3. The data format matches what the system expects

This file is mainly used during development and debugging.
"""

import paho.mqtt.publish as publish
import json

# Sample sensor data used to simulate an ESP32 or external device
payload = {
    "x": 40,
    "y": 35,
    "z": 305
}

# Publish the JSON payload to the MQTT topic on the public broker
publish.single(
    "stephano/motor/data",
    json.dumps(payload),
    hostname="broker.hivemq.com"
)

# Confirmation message to indicate successful publish
print("Message sent")