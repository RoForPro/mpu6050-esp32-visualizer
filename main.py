# main.py

import sys
import argparse
from scripts.training import train_model
from scripts.ui import MainWindow
from PyQt5 import QtWidgets

if __name__=='__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['train','live','offline'], default='live')
    args = p.parse_args()
    if args.mode=='train':
        train_model("data/datos_ejercicio.csv", "models/modelo_prototipo.joblib")
    elif args.mode=='offline':
        import visualizacion_offline
        visualizacion_offline.main()
    else:
        app = QtWidgets.QApplication(sys.argv)
        w = MainWindow("models/modelo_prototipo.joblib", "COM9", 115200)
        w.show()
        sys.exit(app.exec_())
