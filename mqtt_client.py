"""
mqtt_client.py

This file handles real-time data reception from an MQTT broker.

It connects to a public MQTT broker and subscribes to a specific topic
where motor sensor data is published (usually from an ESP32 or external device).

The module is responsible for:
1. Establishing and maintaining MQTT connection
2. Receiving incoming JSON sensor data
3. Storing the latest payload safely for the main system to use
4. Handling reconnection in case of network failure
"""

import json
import threading
import time
import paho.mqtt.client as mqtt

# MQTT broker configuration (public broker used for testing/demo purposes)
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "stephano/motor/data"

# Stores the most recent received MQTT message
# This is shared between threads, so we protect it with a lock
_latest_payload = None
_payload_lock = threading.Lock()


def on_connect(client, userdata, flags, rc):
    """
    Callback function triggered when MQTT client connects to broker.
    """

    if rc == 0:
        print(f"MQTT connected to {BROKER}:{PORT}")

        # Subscribe to the topic once connection is successful
        client.subscribe(TOPIC)
        print(f"Subscribed to topic: {TOPIC}")
    else:
        # Connection failed (non-zero return code)
        print(f"MQTT connection failed with code {rc}")


def on_message(client, userdata, msg):
    """
    Callback function triggered whenever a new message is received
    from the subscribed MQTT topic.
    """

    global _latest_payload

    try:
        # Decode incoming message and convert from JSON string to dictionary
        payload = json.loads(msg.payload.decode("utf-8"))

        # Safely update shared variable using a lock (thread-safe operation)
        with _payload_lock:
            _latest_payload = payload

    except Exception as e:
        # Handle any malformed or corrupted MQTT messages safely
        print(f"MQTT message parse error: {e}")


def get_latest_payload():
    """
    Retrieves the most recent MQTT payload and clears it afterwards.
    This ensures that each payload is only processed once by the system.
    """

    global _latest_payload

    with _payload_lock:
        payload = _latest_payload
        _latest_payload = None

    return payload


def start_mqtt_loop():
    """
    Main MQTT loop that runs in a persistent thread.

    It continuously tries to connect to the broker and keeps listening
    for incoming messages. If connection fails, it automatically retries.
    """

    client = mqtt.Client()

    # Assign callback functions for connection and message handling
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            print("Connecting to MQTT broker...")

            # Establish connection to broker
            client.connect(BROKER, PORT, keepalive=60)

            # Start listening indefinitely (blocking call)
            client.loop_forever()

        except Exception as e:
            # If connection drops, wait a bit and retry
            print(f"MQTT connection error: {e}")
            time.sleep(2)