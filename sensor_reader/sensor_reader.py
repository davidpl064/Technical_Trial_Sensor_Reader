import fire

from sensor_reader.nats_client import NATSClient

class SensorReader():
    def __init__(self, freq_report_data: int, uri_nats_server: str):
        self._freq_report_data = freq_report_data

        # Initialize NATS client
        self._nats_client = NATSClient(uri_nats_server)

    def start_data_publishing(self):
        pass
    def stop_data_publishing(self):
        self._nats_client.disconnect_from_server()
        
    def send_data_to_db(self):
        pass

    def run():
        pass

def main(sensor_type: str, freq_report_data: int, min_range_value: float, max_range_value: float, uri_nats_server: str):
    SensorReader(freq_report_data, uri_nats_server)

if __name__ == '__main__':
     fire.Fire(main)