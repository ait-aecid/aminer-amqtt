#!/usr/bin/env python3
""" MQTT-importer for Aminer

This daemon exports data from mqtt topics and sends it via
unix domain sockets to the logdata-anomaly-miner.
"""

import sys

import os
import socket
import configparser
import logging
import logging.config
import argparse
import signal

sys.path = sys.path[1:]+['/usr/lib/amqtt']
from metadata import __version_string__, __version__  # skipcq: FLK-E402
from amqtt import Amqtt # skipcq: FLK-E402
import ast

CONFIGFILE = '/etc/aminer/amqtt.conf'
unixpath = "/var/lib/amqtt/aminer.sock"
ak = None


def exitgracefully(signum, frame):
    global ak
    ak.close()
    sys.exit(0)

def read_config():
    global CONFIGFILE
    options = dict()
    mqtt_options = dict()
    # GENERAL section allows to use DEFAULT without being
    # added automatically to all the other sections.
    config = configparser.ConfigParser(default_section="GENERAL")
    try:
        config.read(CONFIGFILE)
        options = dict(config.items("DEFAULT"))
        mqtt_options = dict(config.items("MQTT"))
    except:
        options['unixpath'] = unixpath
        options['topics'] = "['aminer']"
        mqtt_options['server'] = "localhost"
        mqtt_options['port'] = "1883"


    if 'MQTT_TOPICS' in os.environ:
        options['topics'] = os.environ.get('MQTT_TOPICS')

    if 'AMQTT_UNIXPATH' in os.environ:
        options['unixpath'] = os.environ.get('AMQTT_UNIXPATH')

    if 'MQTT_SERVER' in os.environ:
        mqtt_options['server'] = os.environ.get('MQTT_SERVER')

    if 'AMQTT_SEARCH' in os.environ:
        options['search'] = os.environ.get('AMQTT_SEARCH')

    if 'AMQTT_FILTERS' in os.environ:
        options['filters'] = os.environ.get('AMQTT_FILTERS')


    return options,mqtt_options


def main():
    global ak
    global unixpath
    global CONFIGFILE
    description="A daemon that polls logs from mqtt-topics and writes it to a unix-domain-socket(for logdata-anomaly-miner)"

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--version', action='version', version=__version_string__)
    args = parser.parse_args()

    options,mqtt_options = read_config()
    logger = False

    try:
        logging.config.fileConfig(CONFIGFILE)
    except KeyError:
        logging.basicConfig(level=logging.DEBUG)

    logger = logging.getLogger()

    for key, val in mqtt_options.items():
        try:
            mqtt_options[key] = int(val)
        except:
            pass

    if options.get('unixpath'):
        unixpath = options.get('unixpath')

    try:
        if os.path.exists(unixpath):
            os.remove(unixpath)
    except PermissionError:
        logger.error("Unable to delete file %s : Permission Denied!" % unixpath)
        exit(1)

    topics = ast.literal_eval(options.get('topics'))

    logger.info("starting amqtt daemon...")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.bind(unixpath)
    except FileNotFoundError:
        logger.error("Path to unix-domain-socket not found: %s" % unixpath)
        exit(1)
    except PermissionError:
        logger.error("Unable to create socket %s : Permission Denied!" % unixpath)
        exit(1)

    ak = Amqtt(*topics,**mqtt_options)

    if options.get('search'):
        ak.searchlist = ast.literal_eval(options.get('search'))
    if options.get('filters'):
        ak.setfilter(options.get('filters'))

    try:
        sock.listen(0)
        while True:
            logger.debug("Socket: Waiting for connection...")
            conn, addr = sock.accept()
            with conn:
                logger.debug("Socket-connection accepted!")
                ak.setsock(conn)
                ak.run()
    except KeyboardInterrupt:
        ak.close()

if __name__=='__main__':
    signal.signal(signal.SIGINT, exitgracefully)
    signal.signal(signal.SIGTERM, exitgracefully)
    signal.signal(signal.SIGUSR1, exitgracefully)
    main()


