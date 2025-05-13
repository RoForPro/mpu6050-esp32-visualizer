# core/imu/manager.py

from typing import List, Dict, Any
from core.imu.imu import IMUSensor

class SensorManager:
    """
    Agrupa varios IMUSensor y permite leerlos de forma unificada.
    """

    def __init__(self, sensor_configs: List[Dict[str, Any]]):
        """
        :param sensor_configs: lista de dicts con claves:
            - 'id': identificador del sensor (str)
            - 'port': puerto serie (str)
            - 'baud_rate': velocidad de comunicación (int)
        """
        self.sensors: List[IMUSensor] = []
        for cfg in sensor_configs:
            sensor = IMUSensor(
                sensor_id=cfg['id'],
                port=cfg['port'],
                baud_rate=cfg.get('baud_rate', 115200)
            )
            self.sensors.append(sensor)

    def read_all(self) -> List[Dict[str, Any]]:
        """
        Extrae **todas** las muestras de cada sensor (llamando a read_now)
        y devuelve una lista de dicts como:
          [ {sensor_id, timestamp, yaw, pitch, roll}, … ]
        """
        readings = []
        for sensor in self.sensors:
            sensor_data = sensor.read_now()   # ahora devuelve lista
            readings.extend(sensor_data)
        return readings

    def close_all(self):
        """
        Detiene y cierra todos los hilos/puertos de los sensores.
        """
        for sensor in self.sensors:
            sensor.close()
