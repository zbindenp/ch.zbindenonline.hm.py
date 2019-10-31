import configparser
import json


def createConfig(args):
    config = configparser.ConfigParser()
    if len(config.read(args.config)) == 0:
        raise FileNotFoundError('ConfigFile not found', args.config)

    default = config['DEFAULT']
    sensors = json.loads(default.get('sensors'))
    brokerConf = BrokerConfig('MyTestClient', default.get('outdoor_weather_uid'), default.get('broker'))
    rest = config['rest']
    restConf = RestConfig(rest.get('url'), rest.get('username'), rest.get('password'))
    picture = config['pictures']
    pictureConf = PicturesConfig(picture.get('client_id'), picture.get('client_secret'), picture.get('username'),
                                 picture.get('password'), picture.get('picture_dir'), picture.get('picture_url'),
                                 picture.get('camera_id'),
                                 picture.get('delete_after_publish'))

    return Config(brokerConf, restConf, pictureConf, args.log.upper(), sensors, default.get('database'))


class Config:
    def __init__(self, broker, rest, pictures, loglevel='INFO', sensors='{}', database='dorben.db'):
        self.loglevel = loglevel
        self.sensors = sensors
        self.broker = broker
        self.database = database
        self.rest = rest
        self.pictures = pictures


class BrokerConfig:
    def __init__(self, clientId, outdoor_weather_uid, broker='localhost', qos=1):
        self.broker = broker
        self.clientId = clientId
        self.outdoor_weather_uid = outdoor_weather_uid
        self.qos = qos


class RestConfig:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password


class PicturesConfig:
    def __init__(self, client_id, client_secret, username, password, picture_dir, picture_url, camera_id,
                 delete_after_publish):
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.picture_dir = picture_dir
        self.picture_url = picture_url
        self.camera_id = camera_id
        self.delete_after_publish = delete_after_publish
