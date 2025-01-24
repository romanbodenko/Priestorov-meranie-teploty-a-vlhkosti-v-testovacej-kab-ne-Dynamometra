import csv
import json
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LogFormat(Enum):
    CSV = "csv"
    JSON = "json"


@dataclass
class SensorReading:
    sensor_id: str
    temperature: float
    humidity: float
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def validate(self) -> bool:
        try:
           return (
                #isinstance(self.sensor_id, str) and
                #isinstance(self.temperature, (int, float)) and
                #isinstance(self.humidity, int, float) and
                0 <= self.humidity <= 100 and
                -50 <= self.temperature <= 100
            )
        except (TypeError, ValueError):
            return False


class SensorLogger:
    def __init__(self, base_path: str = "logs", format: LogFormat = LogFormat.CSV):
        self.base_path = Path(base_path)
        self.format = format
        self.fieldnames = ['timestamp', 'sensor_id', 'temperature', 'humidity']
        self._ensure_log_directory()

    def _ensure_log_directory(self):
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self, date: Optional[datetime] = None) -> Path:
        if date is None:
            date = datetime.now()
        filename = f"sensor_log_{date.strftime('%Y_%m_%d')}.{self.format.value}"
        return self.base_path / filename

    def save_reading(self, reading: SensorReading) -> bool:
        if not reading.validate():
            return False

        if self.format == LogFormat.CSV:
            return self._save_to_csv(reading)
        elif self.format == LogFormat.JSON:
            return self._save_to_json(reading)

    def _save_to_csv(self, reading: SensorReading) -> bool:
        file_path = self._get_log_file_path()
        file_exists = file_path.exists()

        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames, delimiter=';')

            # Ak súbor ešte neexistuje, zapíšeme hlavičky
            if not file_exists:
                writer.writeheader()

            # Zapíšeme riadok
            writer.writerow({
                'timestamp': reading.timestamp.strftime('%Y-%m-%d %H:%M'),
                'sensor_id': reading.sensor_id,
                'temperature': reading.temperature,
                'humidity': reading.humidity
            })
        return True

    def _save_to_json(self, reading: SensorReading) -> bool:
        file_path = self._get_log_file_path()
        data = []

        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

        data.append({
            'timestamp': reading.timestamp.isoformat(),
            'sensor_id': reading.sensor_id,
            'temperature': reading.temperature,
            'humidity': reading.humidity
        })

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)
        return True

    def get_readings(self, date: Optional[datetime] = None) -> List[Dict]:
        file_path = self._get_log_file_path(date)
        if not file_path.exists():
            return []

        if self.format == LogFormat.CSV:
            with open(file_path, mode='r', encoding='utf-8') as file:
                return list(csv.DictReader(file))
        elif self.format == LogFormat.JSON:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)