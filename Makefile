init:
	pip3 install -r requirements.txt

install: init
	test -d /usr/lib/amqtt || mkdir -p /usr/lib/amqtt
	cp -r amqtt/* /usr/lib/amqtt/
	test -d /etc/aminer/ || mkdir /etc/aminer/
	test -e /etc/aminer/amqtt.conf || cp etc/amqtt.conf /etc/aminer/amqtt.conf
	test -d /etc/systemd/system && cp etc/amqttd.service /etc/systemd/system/amqttd.service
	test -d /var/lib/amqtt || mkdir /var/lib/amqtt
	cp bin/amqttd.py /usr/lib/amqtt/amqttd.py
	chmod 755 /usr/lib/amqtt/amqttd.py
	test -e /usr/local/bin/amqttd.py || ln -s /usr/lib/amqtt/amqttd.py /usr/local/bin/amqttd.py

uninstall:
	rm -rf /usr/lib/amqtt
	unlink /usr/local/bin/amqttd.py

