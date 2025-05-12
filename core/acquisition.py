# scripts/acquisition.py

import serial, threading, time, csv
from typing import Callable


class CaptureWidget:
    """
    Lee serie en hilo y notifica callbacks con cada línea decodificada.
    También segmenta por tag con callbacks.
    """

    def __init__(self, port: str, baud: int, raw_csv: str):
        self.port = port
        self.baud = baud
        self.running = False
        self._thread = None
        self.on_line: Callable[[float, float, float, float], None] = None
        # Segment callbacks
        self.on_segment_start: Callable[[str], None] = None
        self.on_segment_end: Callable[[str, list], None] = None
        self.current_tag = None
        self.segment_data = []
        # Raw CSV
        self.raw_csv = raw_csv

    def start(self):
        # Si ya estamos leyendo, no arrancamos otro hilo
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _reader(self):
        ser = serial.Serial(self.port, self.baud, timeout=1)
        time.sleep(2)
        for _ in range(10): ser.readline()
        # Abrir raw CSV
        with open(self.raw_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            while self.running:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line: continue
                parts = line.split(',')
                if len(parts) == 4:
                    ts, y, p, r = map(float, parts)
                    # callback línea
                    if self.on_line: self.on_line(ts, y, p, r)
                    # escribir raw
                    writer.writerow([ts, y, p, r])
                    # segmentación
                    if self.current_tag:
                        self.segment_data.append([ts, y, p, r])
        ser.close()

    def tag_start(self, tag: str):
        """Inicia un segmento con etiqueta tag."""
        if self.current_tag: return
        self.current_tag = tag
        self.segment_data = []
        if self.on_segment_start: self.on_segment_start(tag)

    def tag_end(self):
        """Finaliza segmento y emite callback con datos."""
        if not self.current_tag: return
        data = self.segment_data.copy()
        tag = self.current_tag
        self.current_tag = None
        self.segment_data = []
        if self.on_segment_end: self.on_segment_end(tag, data)
