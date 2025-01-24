from datetime import datetime
import logging
from sensor_logger import SensorLogger, SensorReading, LogFormat
from typing import List, Dict
import configparser
import os
import struct
logger = logging.getLogger(__name__)


class Config:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        self.load_config()

    def load_config(self) -> None:
        if not os.path.exists(self.config_file):
            self.create_default_config()
        self.config.read(self.config_file)

    def create_default_config(self) -> None:
        self.config['Sensors'] = {
            'num_sensors': '20',
            'min_temp': '-15.0',
            'max_temp': '50.0',
            'min_humidity': '0',
            'max_humidity': '100'
        }
        self.config['Logging'] = {
            'log_format': 'csv',
            'log_path': 'sensor_logs'
        }
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)




class SensorDataManager:
    def __init__(self, config: Config, bus, address):
        self.config = config
        self.bus = bus  # I2C zbernica
        self.address = address  # Adresa I2C slave
        self.logger = SensorLogger(
            base_path=config.config['Logging']['log_path'],
            format=LogFormat(config.config['Logging']['log_format'])
        )

    def generate_sensor_data(self) -> List[Dict]:
        """Generuje údaje zo senzorov z dvoch I2C slave zariadení."""
        data = []

        # Cyklus cez všetky slave zariadenia
        for slave_addr in self.address:
            try:
                # Čítanie 20 bajtov
                raw_data = self.bus.read_i2c_block_data(slave_addr, 0, 20)

                for i in range(5):  # 5 senzorov na jednom slave zariadení
                    # Spracovanie údajov: teplota (2 bajty), vlhkosť (2 bajty)
                    temp = struct.unpack('h', bytes(raw_data[i * 4:i * 4 + 2]))[0]
                    hum = struct.unpack('h', bytes(raw_data[i * 4 + 2:i * 4 + 4]))[0]

                    reading = SensorReading(
                        sensor_id=f"Sensor_{slave_addr}_{i + 1}",  # Unikátny identifikátor
                        temperature=temp / 100.0,
                        humidity=hum / 100.0
                    )

                    if reading.validate():
                        self.logger.save_reading(reading)
                        data.append({
                            'Sensor': reading.sensor_id,
                            'Temperature': reading.temperature,
                            'Humidity': reading.humidity,
                            'Timestamp': reading.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                        })
                    else:
                        logger.error(f"Neplatné údaje zo senzora Sensor_{slave_addr}_{i + 1}")

            except Exception as e:
                logger.error(f"Chyba pri čítaní z adresy {slave_addr}: {e}")

        return data


    def get_todays_readings(self) -> List[Dict]:
        return self.logger.get_readings()

    def get_readings_by_date(self, date: datetime) -> List[Dict]:
        return self.logger.get_readings(date)
