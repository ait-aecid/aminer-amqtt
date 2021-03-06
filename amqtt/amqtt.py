"""A Aminer-MQTT importer

This module reads data from a mqtt topic and forwards it 
to a unix-domain socket

"""

import threading
import logging
import json
import copy
import re
import ast
import datetime
from baseplugin import BasePlugin # skipcq: FLK-E402
import threading as th
import paho.mqtt.client as mqtt
from dictfilter import query

class Amqtt:
    DEFAULT_CONFIG = {
        'server': 'localhost',
        'port': '1883',
        'username': None,
        'password': None,
        'ca_cert': None,
        'certfile': None,
        'keyfile': None
    }

    def __init__(self, *topics, **configs):
        self.config = copy.copy(self.DEFAULT_CONFIG)
        self.timer = None
        self.stopper = False
        self.sort = None
        self.sock = None
        self.topics = topics
        self.searchlist = None
        self.filters = False
        self.filters_delim = '.'
        self.check_alive = False
        self.decoder = None
        self.check_interval = 5.0

        self.logger = logging.getLogger(__name__)

        for key in configs:
            self.config[key] = configs[key]

        self.consumer = None
        self.logger.debug(self.sort)

    def setfilter(self, filters):
        if isinstance(filters, str):
            self.filters = ast.literal_eval(filters)
            if not isinstance(self.filters, list):
                self.logger.info("Warning: conf-parameter filters is not a list!")
                self.filters = None

    def displayfilter(self,hit):
        try:
            json_hit = json.loads(hit)
        except json.decoder.JSONDecodeError:
            self.logger.debug("displayfilter: %s" % hit)
            return hit
        except UnicodeDecodeError:
            self.logger.debug("Unicode-Decode-Error")
            return hit

        if self.filters is False:
            self.logger.debug("displayfilter with filters is FALSE: %s" % hit)
            return hit
        else:
            ret = {}
            ret = query(json_hit, self.filters, delimiter=self.filters_delim)
            if ret:
                return json.dumps(ret).encode("ascii")
            else:
                return False

    def setlogger(self, logger):
        """Define a logger for this module
        """
        self.logger = logger

    def search(self, value):
        if isinstance(self.searchlist, list):
            for f in self.searchlist:
                if re.findall(f, str(value)):
                    return True
            return False
        else:
            return True

    def on_connect(self, client, userdata, flags, rc):
        self.logger.debug("Connected...")
        for t in self.topics:
            client.subscribe(t)

    def decode(self, payload):
        if isinstance(self.decoder, BasePlugin):
            self.logger.debug("Decoding Payload")
            return self.decoder.decode(payload)
        return payload

    def handler(self, client, userdata, msg):
        """Scheduler-function that polls mqtt

        """
        try:
            self.logger.debug("Recieved data on topic: %s" % msg.topic)
            payload = self.decode(msg.payload)
            if self.search(payload) is True:
               self.logger.debug(payload)
               data = self.displayfilter(payload)
               if data:
                   self.logger.debug("Sending data: %s" % data)
                   if isinstance(data,str):
                   	self.sock.send(data.encode())
                   else:
                   	self.sock.send(data)
                   self.sock.send('\n'.encode())
        except OSError:       
            self.logger.error("Client disconnected", exc_info=False)
            self.stopper = True

            

    def setsock(self, sock):
        """Setter for the unix-socket
        """
        self.sock = sock

    def timing(self):
        self.check_alive = True

    def run(self):
        """Starts the scheduler
        """
        try:
            self.stopper = False
            self.consumer = mqtt.Client()
            self.consumer.enable_logger(self.logger)
            if self.config['username'] is not None and self.config['password'] is not None:
                self.consumer.username_pw_set(self.config['username'], password=self.config['password'])
            if self.config['ca_cert'] is not None:
                self.logger.debug("Using ca_cert: %s" % self.config['ca_cert'])
                self.consumer.tls_set(ca_certs=self.config['ca_cert'])
            self.consumer.on_connect = self.on_connect
            self.consumer.on_message = self.handler
            self.consumer.connect(self.config['server'],self.config['port'])
            T = th.Timer(self.check_interval, self.timing)
            T.start()
            self.logger.debug("Starting another run with check_interval %f" % self.check_interval)

            while self.stopper is False:
                self.consumer.loop()
                if self.check_alive == True:
                    self.check_alive = False
                    self.sock.send('\n'.encode())
                    T = th.Timer(self.check_interval, self.timing)
                    T.start()
        except KeyboardInterrupt:
            self.logger.debug("KeyboardInterrupt detected...")
            self.stopper = True
        except OSError as error:
            self.logger.error(error)
            self.logger.error("Client disconnected", exc_info=False)
        finally:
            self.close()

    def close(self):
        """Stops the socket and the scheduler
        """
        self.logger.debug("Cleaning up socket and scheduler")
        self.consumer.loop_stop()
        self.consumer.disconnect()
        self.stopper = True
        if self.sock is not None:
            self.logger.debug("Closing socket...")
            self.sock.close()
