import paho.mqtt.client as mqtt
import logging

class TinkerforgeBroker:
    def __init__(self, host, clientId, qos, brickletId):
        self._host = host
        self._mqtt = mqtt.Client(clientId)
        self._qos = qos
        self._topic = "tinkerforge/bricklet/outdoor_weather/{}/sensor_data".format(brickletId)

    def start(self, on_sensor):
        self._mqtt.message_callback_add(self._topic, on_sensor)  # do not include leading slash on topic
        self._mqtt.on_connect = self._on_connect
        self._mqtt.connect(self._host, port=1883, keepalive=60)
        self._mqtt.loop_start()

    def stop(self):
        self._mqtt.loop_stop()
        self._mqtt.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        logging.debug("Connected with result code %s", str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self._mqtt.subscribe([(self._topic, self._qos)])
