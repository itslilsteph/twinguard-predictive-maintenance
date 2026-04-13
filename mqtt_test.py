import paho.mqtt.publish as publish
import json

payload = {
    "x": 40,
    "y": 35,
    "z": 305
}

publish.single(
    "stephano/motor/data",
    json.dumps(payload),
    hostname="broker.hivemq.com"
)

print("Message sent")