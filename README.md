# aminer-amqtt

This daemon polls logs from mqtt topics and writes it to a unix-domain-socket(for [logdata-anomaly-miner](https://github.com/ait-aecid/logdata-anomaly-miner.git))

# Installation

```
sudo make install
```

After that set owner of /var/lib/amqtt to aminer-user:

```
sudo chown aminer:aminer /var/lib/amqtt
```

# Configuration

It is possible to configure amqtt via configuration file which must be located at '/etc/aminer/kafka.conf' or via environment variables. 
A sample of the configuration file can be found at [etc/mqtt.conf](/etc/kafka.conf)
The following environment variables are available:

| Environment variable | Example | Description |
| -------------------- | ------- | ----------- |
| MQTT_TOPICS         | `['aminer','logs']` | List of topics |
| AMQTT_UNIXPATH      | /var/lib/amqtt/aminer.sock | Path to the unix domain socket |
| MQTT_SERVER         | localhost | MQTT server |
| MQTT_PORT           | 1883 | MQTT port |
| MQTT_USERNAME       | user01 | MQTT user |
| MQTT_PASSWORD       | supersecure | MQTT password |
| AMQTT_SEARCH        | `['.*example.com.*']` | List of regex-patterns to filter specific events |
| AMQTT_FILTERS       | `['@metadata.type','@timestamp']` |

# Poll manually

```
sudo /usr/local/bin/amqttd.py
```

# Starting the daemon

```
sudo systemctl enable amqttd
sudo systemctl start amqttd
```

# Testing

Normally the daemon starts polling the elasticsearch as soon as some other programm reads from the unix-domain-socket.
It is possible to read from the socket manually using ncat(from nmap) as follows:

```
sudo ncat -U /var/lib/amqtt/aminer.sock
```

# Uninstall

The following command will uninstall amqtt but keeps the configuration file:
```
sudo make uninstall
```
