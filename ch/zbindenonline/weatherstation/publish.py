import argparse
import logging
import datetime
import requests
import sqlite3
import sys
from .config import *


class RestService:
    def __init__(self, url, username, password):
        self.url = url
        self.auth = {'username': username, 'password': password}
        self.headers = {'User-Agent': 'python'}
        self.login()

    def login(self):
        logging.debug("Try to login to " + self.url + '/login')
        try:
            response = requests.post(self.url + '/login', data=json.dumps(self.auth), headers=self.headers)
        except requests.exceptions.RequestException as e:
            logging.exception("RequestException occured: " + str(e))
            sys.exit(1)

        if not response.ok:
            response.raise_for_status()
        str_response = response.content.decode('utf-8')
        logging.debug(str_response)
        if str_response:
            jwtdata = json.loads(str_response)
            jwt = jwtdata['access_jwt']
            logging.info(jwt)
            self.headers['Authorization'] = 'Bearer ' + jwt

    def get_sensors(self):
        response = requests.get(self.url + '/sensors', headers=self.headers)
        logging.info(response)
        if response.ok:
            str_response = response.content.decode('utf-8')
            logging.debug(str_response)
            return json.loads(str_response)
        else:
            response.raise_for_status()

    def get_last_timestamp(self, sensorId):
        response = requests.get(self.url + '/measures/last?sensor=' + sensorId, headers=self.headers)
        if response.ok:
            str_response = response.content.decode('utf-8')
            logging.debug(str_response)
            if str_response:
                last = json.loads(str_response)
                return last['measured_at']
            return '1970-01-01 00:00'
        else:
            response.raise_for_status()

    def post_measure(self, measure):
        logging.debug('Headers:')
        logging.debug(self.headers)
        response = requests.post(self.url + '/measures', data=measure, headers=self.headers)
        logging.debug(response)
        if not response.ok:
            response.raise_for_status()


def read_configuration():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--wait", help="wait in seconds between publish", type=int, default=300)
    parser.add_argument("-c", "--config", help="config file", type=str, default='weatherstation.cfg')
    parser.add_argument("-l", "--log", help="level to log", type=str, default="INFO")
    args = parser.parse_args()
    return createConfig(args)


def configure_logging(loglevel):
    numeric_level = getattr(logging, loglevel, "INFO")
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=numeric_level)


def main():
    start = datetime.datetime.now()
    config = read_configuration()
    configure_logging(config.loglevel)
    try:
        conn = sqlite3.connect(config.database)
        headers = {'User-Agent': 'python'}
        service = RestService(config.rest.url, config.rest.username, config.rest.password)
        sensors = service.get_sensors()
        postedMeasures = 0;
        for sensor in sensors:
            sensorId = sensor['id']
            last = service.get_last_timestamp(sensorId)
            logging.debug(sensor['name'])
            logging.debug(last)
            with conn:
                cur = conn.cursor()
                # logging.info("SELECT m.created_at, m.temperature, m.humidity from measure m join sensor s on s.id=m.sensor where s.name=? and m.created_at > datetime(?, '+1 second')");
                # logging.info((sensor['name'], last))
                cur.execute(
                    "SELECT m.created_at, m.temperature, m.humidity from measure m join sensor s on s.id=m.sensor where s.name=? and m.created_at > datetime(?, '+1 second')",
                    (sensor['name'], last))
                measures = cur.fetchall()
                measuresData = []
                measuresJson = []
                measuresPerSensor = 0
                for measure in measures:
                    # logging.info(measure)
                    data = {'sensor': sensorId, 'measured_at': measure[0], 'temperature': str(measure[1]),
                            'humidity': str(measure[2])}
                    json_data = json.dumps(data)
                    measuresData.append(data)
                    measuresPerSensor += 1
                # logging.info(json.dumps(measuresData))
                if len(measures) > 0:
                    logging.info('Posting ' + str(measuresPerSensor) + " for sensor '" + sensor['name'] + "'")
                    service.post_measure(json.dumps(measuresData))
                    postedMeasures += measuresPerSensor
        elapsed_time = datetime.datetime.now() - start
        logging.info('Posted ' + str(postedMeasures) + ' in ' + str(elapsed_time))
    except Exception as e:
        logging.error("Error occurred: " + str(e))


if __name__ == '__main__':
    main()
