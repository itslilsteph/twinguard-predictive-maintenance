import json
import threading
import time
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "stephano/motor/data"

_latest_payload = None
_payload_lock = threading.Lock()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"MQTT connected to {BROKER}:{PORT}")
        client.subscribe(TOPIC)
        print(f"Subscribed to topic: {TOPIC}")
    else:
        print(f"MQTT connection failed with code {rc}")


def on_message(client, userdata, msg):
    global _latest_payload

    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        with _payload_lock:
            _latest_payload = payload

    except Exception as e:
        print(f"MQTT message parse error: {e}")


def get_latest_payload():
    global _latest_payload

    with _payload_lock:
        payload = _latest_payload
        _latest_payload = None

    return payload


def start_mqtt_loop():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            print("Connecting to MQTT broker...")
            client.connect(BROKER, PORT, keepalive=60)
            client.loop_forever()
        except Exception as e:
            print(f"MQTT connection error: {e}")
            time.sleep(2)