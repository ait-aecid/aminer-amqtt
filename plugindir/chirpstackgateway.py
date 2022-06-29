import sys
import json
from datetime import datetime,timezone,timedelta
from chirpstack_api.gw import UplinkFrame

sys.path = sys.path[1:]+['/usr/lib/amqtt']

from baseplugin import BasePlugin

class Decoder(BasePlugin):
    def __init__(self,options) :
        print("loading plugin")
        super().__init__(options)
        self.tzoffset = 0 # UTC
        if options.get('tzoffset'):
            self.tzoffset = int(options.get('tzoffset'))

    def decode(self,payload):
        jlo = {}
        frame = UplinkFrame()
        frame.ParseFromString(payload)
        timestamp = datetime.now(timezone(timedelta(hours=self.tzoffset)))
        jlo = { 
            'timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S%z"),
            'phy_payload': frame.phy_payload.hex(), 
            'tx_info': {
                'frequency': str(frame.tx_info.frequency), 
                 'lora_modulation_info': {
                     'bandwidth': str(frame.tx_info.lora_modulation_info.bandwidth),
                     'spreading_factor': str(frame.tx_info.lora_modulation_info.spreading_factor),
                     'code_rate': str(frame.tx_info.lora_modulation_info.code_rate)
                 }
            },
            'rx_info': {
                'gateway_id': frame.rx_info.gateway_id.hex(),
                'rssi': str(frame.rx_info.rssi),
                'lora_snr': str(frame.rx_info.lora_snr),
                'rf_chain': str(frame.rx_info.rf_chain),
                'context': frame.rx_info.context.hex(),
                'uplink_id': frame.rx_info.uplink_id.hex(),
                'crc_status': str(frame.rx_info.crc_status)
            }
        }
        return json.dumps(jlo)
