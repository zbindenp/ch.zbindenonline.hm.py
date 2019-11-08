import argparse
import datetime
import logging
import os
import sys
from pathlib import Path

import requests

from .config import *


class RestService:
    def __init__(self, url, camera_id, client_id, client_secret, username, password):
        self.url = url
        self.camera_id = camera_id
        self.auth = {'grant_type': 'password', 'client_id': client_id, 'client_secret': client_secret,
                     'username': username, 'password': password}
        self.headers = {'User-Agent': 'python'}
        self.login()

    def login(self):
        logging.debug("Try to login to " + self.url + '/oauth/token')
        logging.debug(json.dumps(self.auth))
        try:
            loginHeaders = {'Content-Type': 'application/json'}
            response = requests.post(self.url + '/oauth/token', data=json.dumps(self.auth), headers=loginHeaders,
                                     timeout=20)
        except requests.exceptions.RequestException as e:
            logging.exception("RequestException occured: " + str(e))
            sys.exit(1)

        if not response.ok:
            response.raise_for_status()
        str_response = response.content.decode('utf-8')
        logging.debug(str_response)
        if str_response:
            jwtdata = json.loads(str_response)
            jwt = jwtdata['access_token']
            logging.info(jwt)
            self.headers['Authorization'] = 'Bearer ' + jwt

    def post_picture(self, picture):
        logging.debug('Headers:')
        logging.debug(self.headers)
        filename = Path(picture).with_suffix('').name
        taken_at = datetime.datetime.strptime(filename, '%Y-%m-%d_%H%M')
        logging.debug(taken_at)
        picture_data = {'taken_at': taken_at.strftime("%Y-%m-%d %H:%M:%S")}
        logging.debug(picture_data)
        file = {'image': open(picture, 'rb')}
        response = requests.post(self.url + '/cameras/' + self.camera_id + '/pictures', files=file, data=picture_data,
                                 headers=self.headers, timeout=120)
        logging.debug(response)
        if not response.ok:
            json_data = json.loads(response.text)
            logging.error(json_data)
            response.raise_for_status()


def read_configuration():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--wait", help="wait in seconds between publish", type=int, default=300)
    parser.add_argument("-c", "--config", help="config file", type=str, default='weatherstation.cfg')
    parser.add_argument("-l", "--log", help="level to log", type=str, default="INFO")
    args = parser.parse_args()
    return createConfig(args)


def get_pictures(picture_dir):
    logging.info('Parsing ' + picture_dir)
    files = list()
    for file in os.listdir(picture_dir):
        if file.endswith('.jpg'):
            files.append(os.path.join(picture_dir, file))
    return files


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
        service = RestService(config.pictures.picture_url, config.pictures.camera_id, config.pictures.client_id,
                              config.pictures.client_secret,
                              config.pictures.username, config.pictures.password)
        pictures = get_pictures(config.pictures.picture_dir);
        postedPictures = 0;
        for picture in pictures:
            logging.debug('Try to publish ' + picture)
            try:
                service.post_picture(picture)
                postedPictures += 1
                if config.pictures.delete_after_publish:
                    logging.debug('Delete ' + picture)
                    os.remove(picture)
            except Exception as e:
                logging.warning('There was en Exception in posting picture' + str(e))

        elapsed_time = datetime.datetime.now() - start
        logging.info('Posted ' + str(postedPictures) + ' in ' + str(elapsed_time))
    except Exception as e:
        logging.error("Error occurred: " + str(e))


if __name__ == '__main__':
    main()
