import time
import datetime
import logging
import argparse
import sqlite3
from .mqtt import TinkerforgeBroker
from .config import *

waitForSensors = 10


class SensorData:
    def __init__(self, identifier, temperature, humidity):
        self.identifier = identifier
        self.temperature = temperature
        self.humidity = humidity

    def __str__(self):
        return "SensorData[" + self.identifier + "]: [" + str(self.temperature) + "°C], [" + str(self.humidity) + "%]"


class DataHandler:
    def __init__(self, sensor_mapping):
        self._sensor_mapping = sensor_mapping
        self.sensors = None

    def on_sensor_temp(self, mosq, obj, msg):
        try:
            self.sensors = list()
            sensorsdata = json.loads(msg.payload.decode('utf-8'))
            for x in sensorsdata:
                if x in self._sensor_mapping:
                    sensor = SensorData(x, sensorsdata[str(x)]["temperature"] / 10, sensorsdata[str(x)]["humidity"])
                    self.sensors.append(sensor)
        except Exception as e:
            logging.error(e)
            self.sensors = None


def readConfiguration():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--wait", help="wait in seconds between publish", type=int, default=300)
    parser.add_argument("-c", "--config", help="config file", type=str, default='weatherstation.cfg')
    parser.add_argument("-l", "--log", help="level to log", type=str, default="INFO")
    args = parser.parse_args()
    return createConfig(args)


def configureLogging(logLevel):
    numeric_level = getattr(logging, logLevel, "INFO")
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % logLevel)
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=numeric_level)


def saveToDatabase(database, sensors, sensor_mapping):
    logging.info('Save to database')
    conn = sqlite3.connect(database)
    timestamp = datetime.datetime.now()
    with conn:
        sensorsMap = dict(map(reversed, conn.execute('select id, name from sensor')))
        logging.info(sensorsMap)
        for sensor in sensors:
            temp = sensor.temperature
            hum = sensor.humidity
            conf_name = sensor_mapping.get(sensor.identifier)['name']
            sens = sensorsMap.get(conf_name)
            if sens is None:
                cur = conn.cursor()
                cur.execute('INSERT OR IGNORE INTO sensor(name) values(?)', (conf_name,))
                sens = cur.lastrowid
                logging.debug('Inserted sensor %s with name %s', sens, conf_name)
            conn.execute('INSERT INTO measure(created_at, temperature, humidity, sensor) values(?, ?, ?, ?)',
                         (timestamp, temp, hum, sens))


def configureDatabase(database):
    logging.debug('Configure database')
    conn = sqlite3.connect(database)
    with conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS sensor (
                id INTEGER PRIMARY KEY,
                                   name TEXT NOT NULL
                )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS measure (
             id INTEGER PRIMARY KEY,
             created_at TIMESTAMP NOT NULL,
             temperature real NOT NULL,
             humidity real NOT NULL,
             sensor INTEGER NOT NULL REFERENCES sensor(id)
            )''')


def connectToBroker(brokerConfig, datahandler):
    broker = TinkerforgeBroker(brokerConfig.broker, brokerConfig.clientId, brokerConfig.qos,
                               brokerConfig.outdoor_weather_uid)
    broker.start(datahandler.on_sensor_temp)
    return broker


def main():
    config = readConfiguration()
    configureLogging(config.loglevel)
    configureDatabase(config.database)

    datahandler = DataHandler(config.sensors)
    broker = connectToBroker(config.broker, datahandler)
    try:
        for x in range(waitForSensors):
            try:
                if datahandler.sensors is not None:
                    saveToDatabase(config.database, datahandler.sensors, config.sensors)
                    break

            except (EOFError, SystemExit, KeyboardInterrupt) as e:
                logging.error(e)
            except Exception as e:
                logging.error("Hoppla: " + str(e))
                # sys.exit()
            time.sleep(1)

    finally:
        broker.stop()


if __name__ == '__main__':
    main()
