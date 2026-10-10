import configparser
import os

def amqp_connection_string():
    config = configparser.ConfigParser()

    config.read(os.path.join(os.path.dirname(__file__),"config.ini"))

    config.sections()

    return ("amqps://" +
            config["CONNECTION"]["USER_PASSWORD"] +
            "@" +
            config["CONNECTION"]["SERVER"] +
            ":" +
            config["CONNECTION"]["PORT"] +
            "/" +
            config["CONNECTION"]["VHOST"])
